
## 图片
支持 JPG/JPEG、PNG、WebP。

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

## 分类
在 artworks.json 对应图片的信息里添加 `"category": "茶吧"`。网页自动生成分类按钮。大图左右切换仅浏览当前分类；未分类作品保留在“全部”中，也可以通过“未分类”查看。

## 画作版权
site.json 中 copyrightHolder、rights 和 rightsEnglish 控制画作署名与中英版权说明，显示在页脚和大图下方。name 控制网站标题。画作保留所有权利。
