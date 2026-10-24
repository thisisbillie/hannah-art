# 绘画作品集 · GitHub Pages
暖白底、少文字、原比例作品、点击大图、左右键翻页、手机适配。不调用外部字体或 CDN。未包含示例画作，也没有使用截图中的低清缩略图代替原作。

## 第一次上线
1. 在 GitHub 创建 **Public** 仓库，名称如 `art-portfolio`，默认分支用 `main`。
2. 解压下载包，把 **art-portfolio 文件夹里面的内容** 上传到仓库根目录，不要上传 ZIP，也不要多套一层目录。
3. 必须包含 `.github/workflows/pages.yml`。Mac Finder 按 Command + Shift + . 显示隐藏文件夹。若网页拖拽遗漏了它，可在 GitHub 点 Add file → Create new file，文件名填 `.github/workflows/pages.yml`，复制本地同名文件全部内容。
4. 在仓库 Settings → Pages → Build and deployment → Source 选择 **GitHub Actions**。
5. 编辑 `site.json`，把 name 改为作者名字；bio 可保持空字符串，关于按钮会自动隐藏。
6. 打开 `images` 文件夹，点 Add file → Upload files，上传作品图片并 Commit changes。
7. 查看 Actions → Publish gallery，完成后在 Settings → Pages 获取网址。若之前运行失败，设置完成后在 Actions 中选择 Run workflow 再运行。

以后只需往 images 上传图片，每次提交会自动生成网页、压缩图片并发布。文件名就是作品名，支持中文。修改或删除图片也会触发更新。仓库根目录的 index.html 是模板；正式发布的是 Actions 生成的 _site 内容。

## 图片
支持 JPG/JPEG、PNG、WebP。请用原始作品文件，不用文件夹截图。网页上传单文件建议小于 20 MB；很多图片可分批提交。HEIC 先导出 JPEG。原图留在仓库，发布站点仅包含 900px 缩略图及最长边 3000px 大图，不会放大低分辨率源图。浏览器提前预留固定展示空间，不裁剪画面。首屏优先加载前三张，其余按需加载，大图点击后才加载。
注意：Public 仓库中的原图也公开可访问。如果不想公开原图，请上传自己准备好的展示版本；本地另存真正原稿。PNG 透明背景会转为 RGB，建议上传前先铺好所需底色。

## 可选：作品信息与排序
编辑 artworks.json，键名必须与 images 文件名完全一致；没有配置的图片仍会自动出现。默认按文件名排序，order 越小越靠前：
```json
{
  "烟斗女人.jpg": {
    "title": "烟斗女人",
    "year": "2025",
    "medium": "数码绘画",
    "size": "",
    "description": "",
    "order": 1
  }
}
```
不要填写未经作者确认的年份、媒介或说明。初始页面空白是正常的，上传图片才出现作品。

## 本地预览（可选）
安装 Python 3 后，在仓库目录执行：
```
python3 -m pip install -r requirements.txt
python3 scripts/build.py
python3 -m http.server 8000 --directory _site
```
浏览器打开 http://localhost:8000 。

## 文件结构
- index.html / style.css / app.js：页面、样式和交互
- site.json：作者名字与简介
- artworks.json：可选作品信息
- images/：上传画作
- scripts/build.py：生成图片与作品清单
- .github/workflows/pages.yml：自动部署

GitHub Pages 的大陆访问速度仍取决于网络，本模板无法解决托管域名的连通问题。模板没有站点分析或访客追踪。
