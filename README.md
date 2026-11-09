
## 图片
仓库 images/ 支持 JPG/JPEG、PNG、WebP。飞书上传另外支持 iPhone 的 HEIC/HEIF 图片，构建时自动转换为网站用的 WebP；无需手动转换附件。

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

未启用飞书同步时，通过 `artworks.json` 维护信息。启用后由飞书作品库维护，仓库内旧图片和信息不再参与网站生成。仓库及网站上的作品信息是公开的，请只填写愿意公开的内容。

## 画作版权
site.json 中 copyrightHolder、rights 和 rightsEnglish 控制画作署名与中英版权说明，显示在页脚和大图下方。name 控制网站标题。画作保留所有权利。


## 飞书自动同步

已连接的作品库和字段映射写在 `feishu.json`。这里没有密码。应用需具备知识库节点读取、多维表格读取及附件下载权限，并被授权阅读这份作品库；权限变更后需发布应用版本。

一次性启用步骤：

1. 在飞书补充必需的“展示状态”单选列（草稿、发布），把希望公开的作品设为“发布”。“画作”列必须是附件类型。一条记录代表一幅作品，多张附件时只使用第一张。可选列和名称见 `feishu.json`；情绪、工具、设备使用多选，创作时间使用文本。
2. GitHub 仓库 Settings → Secrets and variables → Actions → New repository secret。名称填写 `FEISHU_APP_SECRET`，值填写飞书应用的 App Secret。App ID 已配置，无需另存。不要把 Secret 放进代码、表格或截图。
3. Actions → Publish gallery → Run workflow，分支选 main。检查构建日志；首次成功后查看网站，确认作品、情绪和图片均正确。

启用 Secret 后，所有部署以飞书为作品来源，只公开“展示状态”精确等于“发布”的记录。“草稿”和空白状态不会展示。已公开作品改回草稿或从表里删除后，会在下次成功同步时从网站移除；此前已公开的图片可能仍留在访客缓存中。没有发布作品时，画廊会变为空画廊。

字段表：作品名、画作、创作时间、创作时的情绪、绘画工具、创作设备、软件或材料、系列、创作小记、展示状态。除了画作和展示状态，其余列允许缺省；作品名为空时显示“未命名”。可选信息会出现在大图详情中。每幅作品由飞书记录 ID 识别，标题可以随时更改，情绪可以多选或留空。仅复制列出的公开字段，不导出完整飞书表格。

工作流每小时第 17 分钟检查一次，GitHub 调度可能延迟。定时检查发现已发布内容未变时，跳过图片下载与部署，以减少调用量。有变化时生成新站点；读取、权限或图片错误会停止部署，原线上站点保持不变。手动 Run workflow 总是重新构建。原始附件只存在于运行器的临时目录，网站产物仅含缩略图、高清 WebP 和公开信息，不包含访问凭证和飞书草稿。

未配置 Secret 时，推送和手动构建继续展示仓库原有画作，定时任务跳过。若已启用同步后删除 Secret，下一次手动或推送部署将恢复仓库原有画作。

公开仓库连续 60 天没有仓库活动时，GitHub 可能停用定时工作流，需要到 Actions 重新启用。飞书免费 API 与存储都有额度；只在有变化时下载图片，按实际用量调整检查频率。不要启用付费运行器。

本地测试：`python3 -m unittest discover -s scripts -p 'test_*.py'`。本地预览默认使用仓库画作；设置环境变量 `FEISHU_APP_SECRET` 后可执行 `python3 scripts/build.py --feishu` 预览飞书公开作品，请勿把凭证写进命令历史。
