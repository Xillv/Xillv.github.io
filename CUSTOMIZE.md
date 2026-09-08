# 个人主页定制清单

这是一个可以直接部署到 GitHub Pages 的 AcadHomepage 模板，版式与参考主页相同。建议按下面的顺序替换信息。

## 1. 基本资料

在 `_config.yml` 中填写：

- `title`：英文姓名
- `description`：一句话身份或研究方向
- `repository`：`GitHub用户名/GitHub用户名.github.io`
- `author.name`：姓名
- `author.bio`：职位与单位
- `author.location`：所在城市和国家
- `author.employer`：单位名称
- `author.email`：公开联系邮箱
- Google Scholar、GitHub、ORCID、DBLP、LinkedIn 等主页链接

将方形个人照片放入 `images/`，然后修改 `author.avatar`。推荐至少 512×512 像素。

## 2. 页面正文

- `_pages/about.md`：个人简介、研究兴趣、荣誉、教育经历与学术服务
- `_pages/news.md`：最新动态，按时间倒序排列
- `_pages/publications.md`：代表论文和完整论文列表
- `_data/navigation.yml`：顶部导航标题与顺序

可以复制 `paper-box` 块来增加带预览图的代表论文。论文图片放入 `images/`。

## 3. 自动更新 Google Scholar 引用数

1. 在 `_config.yml` 中填好 `repository` 和 `author.googlescholar`。
2. 将 `google_scholar_stats_enabled` 改成 `true`。
3. 在 GitHub 仓库的 **Settings → Secrets and variables → Actions** 中添加名为 `GOOGLE_SCHOLAR_ID` 的 secret，值为 Scholar 链接中 `user=` 后面的 ID。
4. 在 GitHub 的 **Actions** 页面启用工作流。

## 4. 本地预览

安装 Ruby、Bundler 和项目依赖后运行：

```bash
bundle install
bundle exec jekyll serve --livereload
```

然后打开 <http://127.0.0.1:4000>。

## 5. 发布到 GitHub Pages

1. 在 GitHub 新建名为 `你的用户名.github.io` 的公开仓库。
2. 在本目录运行：

```bash
git remote add origin https://github.com/你的用户名/你的用户名.github.io.git
git push -u origin main
```

3. 在仓库 **Settings → Pages** 中确认从 `main` 分支发布。

网站通常会出现在 `https://你的用户名.github.io`。

## 需要准备给我的资料

为了把占位内容替换成你的正式主页，请提供：中英文姓名、头像、当前职位与单位、教育经历、研究方向、个人简介、公开邮箱、Scholar/GitHub/ORCID/DBLP 链接、论文列表、动态、奖项以及学术服务。BibTeX、CV、Google Scholar 链接或现有简历都可以直接作为输入。
