"""Fetch public Google Scholar profile statistics without third-party packages."""

from __future__ import annotations

from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


SCHOLAR_ID = os.environ.get("GOOGLE_SCHOLAR_ID", "UiWugpoAAAAJ").strip()
BADGE_ENDPOINT = os.environ.get("GOOGLE_SCHOLAR_BADGE_ENDPOINT", "").strip()
PROFILE_URL = (
    "https://scholar.google.com/citations"
    f"?hl=en&user={SCHOLAR_ID}&view_op=list_works&sortby=pubdate"
    "&cstart=0&pagesize=100"
)
USER_AGENTS = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15",
)


def clean_markup(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    return " ".join(html.unescape(value).split())


def fetch_profile() -> str:
    if not SCHOLAR_ID:
        raise RuntimeError("GOOGLE_SCHOLAR_ID is empty")

    last_error: Exception | None = None
    for attempt in range(4):
        request = Request(
            PROFILE_URL,
            headers={
                "User-Agent": USER_AGENTS[attempt % len(USER_AGENTS)],
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                page = response.read().decode("utf-8", errors="replace")
            if 'id="gsc_prf_in"' in page and 'class="gsc_rsb_std"' in page:
                return page
            last_error = RuntimeError(
                "Google Scholar returned a consent, CAPTCHA, or incomplete page"
            )
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc

        if attempt < 3:
            time.sleep(2 ** attempt)

    raise RuntimeError(f"Unable to fetch Google Scholar profile: {last_error}")


def parse_profile(page: str) -> dict:
    name_match = re.search(
        r'<div[^>]+id="gsc_prf_in"[^>]*>(.*?)</div>', page, re.DOTALL
    )
    stats = [
        int(value.replace(",", ""))
        for value in re.findall(r'<td class="gsc_rsb_std">([\d,]+)</td>', page)
    ]
    if not name_match or len(stats) < 6:
        raise RuntimeError("Scholar profile statistics could not be parsed")

    affiliation_match = re.search(
        r'<div class="gsc_prf_il">(.*?)</div>', page, re.DOTALL
    )
    publications: dict[str, dict] = {}

    for row in re.findall(
        r'<tr class="gsc_a_tr"[^>]*>(.*?)</tr>', page, re.DOTALL
    ):
        title_match = re.search(
            r'<a (?P<attributes>[^>]*class="gsc_a_at"[^>]*)>'
            r'(?P<title>.*?)</a>',
            row,
            re.DOTALL,
        )
        href_match = (
            re.search(r'href="([^"]+)"', title_match.group("attributes"))
            if title_match
            else None
        )
        if not title_match or not href_match:
            continue

        href = html.unescape(href_match.group(1))
        citation_id = parse_qs(urlparse(href).query).get("citation_for_view", [""])[0]
        publication_id = citation_id.split(":", 1)[-1]
        if not publication_id:
            continue

        citation_match = re.search(
            r'<a[^>]+class="[^"]*gsc_a_ac[^"]*"[^>]*>(.*?)</a>',
            row,
            re.DOTALL,
        )
        citation_text = clean_markup(citation_match.group(1)) if citation_match else ""
        citation_count = int(citation_text.replace(",", "")) if citation_text else 0
        gray_fields = [
            clean_markup(value)
            for value in re.findall(r'<div class="gs_gray">(.*?)</div>', row, re.DOTALL)
        ]
        year_match = re.search(r'<span class="gsc_a_h[^>]*>(\d{4})</span>', row)

        publications[publication_id] = {
            "author_pub_id": citation_id,
            "bib": {
                "title": clean_markup(title_match.group("title")),
                "author": gray_fields[0] if gray_fields else "",
                "venue": gray_fields[1] if len(gray_fields) > 1 else "",
                "pub_year": year_match.group(1) if year_match else "",
            },
            "num_citations": citation_count,
        }

    return {
        "scholar_id": SCHOLAR_ID,
        "name": clean_markup(name_match.group(1)),
        "affiliation": clean_markup(affiliation_match.group(1))
        if affiliation_match
        else "",
        "citedby": stats[0],
        "citedby5y": stats[1],
        "hindex": stats[2],
        "hindex5y": stats[3],
        "i10index": stats[4],
        "i10index5y": stats[5],
        "updated": datetime.now(timezone.utc).isoformat(),
        "publications": publications,
    }


def fetch_badge_profile(endpoint: str) -> dict:
    """Read the total from a Scholar-aware endpoint when Google blocks CI IPs."""
    separator = "&" if "?" in endpoint else "?"
    url = f"{endpoint}{separator}user={SCHOLAR_ID}"
    request = Request(url, headers={"User-Agent": USER_AGENTS[0]})
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to fetch citation badge endpoint: {exc}") from exc

    citation_text = str(payload.get("message", "")).replace(",", "").strip()
    if not citation_text.isdigit():
        raise RuntimeError("Citation badge endpoint returned an invalid count")

    return {
        "scholar_id": SCHOLAR_ID,
        "name": "Luwei Xiao",
        "affiliation": "",
        "citedby": int(citation_text),
        "citedby5y": None,
        "hindex": None,
        "hindex5y": None,
        "i10index": None,
        "i10index5y": None,
        "updated": datetime.now(timezone.utc).isoformat(),
        "publications": {},
    }


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary_path.replace(path)


def main() -> None:
    # Google blocks requests from many CI data-center IPs. The scheduled workflow
    # therefore uses a Scholar-aware endpoint; local runs can still parse the full
    # public profile directly by leaving GOOGLE_SCHOLAR_BADGE_ENDPOINT unset.
    profile = (
        fetch_badge_profile(BADGE_ENDPOINT)
        if BADGE_ENDPOINT
        else parse_profile(fetch_profile())
    )
    results = Path(__file__).resolve().parent / "results"
    write_json(results / "gs_data.json", profile)
    write_json(
        results / "gs_data_shieldsio.json",
        {
            "schemaVersion": 1,
            "label": "citations",
            "message": str(profile["citedby"]),
            "color": "9cf",
        },
    )
    print(
        f"Fetched {profile['name']}: {profile['citedby']} citations, "
        f"{len(profile['publications'])} publication records"
    )


if __name__ == "__main__":
    main()
