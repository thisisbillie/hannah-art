
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

## 创作时的情绪与系列
`emotions` 是可填写多个值的情绪标签，允许留空；请由作者本人填写，不根据画面推测。`series` 是选填的作品系列，如“茶吧”。旧的 `category` 字段仍兼容。

```json
{
  "作品文件名.jpeg": {
    "emotions": ["平静", "思念"],
    "series": "茶吧"
  }
}
```

网页自动生成“创作时的情绪”筛选按钮。一幅画可以出现在多个情绪下；“系列”独立筛选，两项同时选择时显示同时符合的作品。大图左右切换仅浏览筛选结果，详情显示已填写的情绪与系列。未填写情绪的作品仍显示在“全部”和“未填写”下。

目前通过 `artworks.json` 维护信息，尚无登录、上传或在线编辑后台。仓库及网站上的作品信息是公开的，请只填写愿意公开的内容。

## 画作版权
site.json 中 copyrightHolder、rights 和 rightsEnglish 控制画作署名与中英版权说明，显示在页脚和大图下方。name 控制网站标题。画作保留所有权利。

