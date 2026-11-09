"""Read published artworks from Feishu; credentials and originals never enter the site."""
import hashlib
import io
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

API = 'https://open.feishu.cn/open-apis'
MAX_IMAGE_BYTES = 50 * 1024 * 1024


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(newurl).scheme != 'https':
            raise RuntimeError('拒绝非 HTTPS 图片下载地址。')
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected and urllib.parse.urlsplit(req.full_url).netloc != urllib.parse.urlsplit(newurl).netloc:
            redirected.remove_header('Authorization')
        return redirected


class Client:
    def __init__(self, app_id, secret):
        self.token = None
        self.opener = urllib.request.build_opener(SafeRedirect())
        data = self.json('/auth/v3/tenant_access_token/internal', payload={'app_id': app_id, 'app_secret': secret})
        self.token = data.get('tenant_access_token')
        if not self.token:
            raise RuntimeError('飞书未返回访问令牌，请检查应用凭证与发布状态。')

    def request(self, path, *, payload=None, query=None, binary=False):
        url = API + path
        if query:
            url += '?' + urllib.parse.urlencode(query)
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        body = json.dumps(payload).encode() if payload is not None else None
        for attempt in range(3):
            try:
                with self.opener.open(urllib.request.Request(url, data=body, headers=headers), timeout=45) as response:
                    limit = MAX_IMAGE_BYTES if binary else 10 * 1024 * 1024
                    content = response.read(limit + 1)
                    if len(content) > limit:
                        raise RuntimeError('飞书返回内容过大；单张图片上限为 50 MB。')
                    # Media API may return an API error as JSON with HTTP 200.
                    if binary and 'json' not in response.headers.get('Content-Type', '').lower():
                        return content
                    try:
                        result = json.loads(content)
                    except (ValueError, UnicodeDecodeError):
                        raise RuntimeError('飞书返回了无法识别的数据。') from None
                    code = result.get('code', 0)
                    if code != 0:
                        raise RuntimeError(f'飞书接口错误（代码 {code}）；请检查应用权限、发布状态和作品库访问权限。')
                    if binary:
                        raise RuntimeError('飞书未返回图片内容，请检查附件下载权限。')
                    return result
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f'飞书请求失败（HTTP {exc.code}），本次不部署，原网站保持不变。') from None
            except (urllib.error.URLError, TimeoutError):
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError('连接飞书超时或网络异常，本次不部署。') from None

    def json(self, path, **kwargs):
        return self.request(path, **kwargs)

    def items(self, path):
        page_token = None
        seen = set()
        while True:
            query = {'page_size': 100}
            if page_token:
                query['page_token'] = page_token
            data = self.json(path, query=query)['data']
            items = data.get('items', [])
            if not isinstance(items, list):
                raise RuntimeError('飞书列表数据格式异常。')
            yield from items
            if not data.get('has_more'):
                break
            page_token = data.get('page_token')
            if not page_token or page_token in seen:
                raise RuntimeError('飞书分页信息异常，停止同步以防遗漏作品。')
            seen.add(page_token)


def text(value):
    if value is None:
        return ''
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return ''.join(text(item) for item in value).strip()
    if isinstance(value, dict) and isinstance(value.get('text'), str):
        return value['text'].strip()
    raise RuntimeError('作品文本字段类型不符，请将创作时间等文本字段设为文本类型。')


def tags(value):
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise RuntimeError('情绪、工具和设备字段应设置为多选类型。')
    return list(dict.fromkeys(item.strip() for item in value if item.strip()))


def select_published(records, config):
    names = config['fields']
    result = []
    for record in records:
        fields = record.get('fields', {})
        # Draft fields and attachments are never mapped or downloaded.
        if text(fields.get(names['status'])) != config['publishedValue']:
            continue
        images = fields.get(names['image'])
        if not isinstance(images, list) or not images or not images[0].get('file_token'):
            raise RuntimeError('有标为发布的作品缺少画作附件；请补图或改回草稿。')
        info = {key: text(fields.get(names[key])) for key in ('title', 'year', 'medium', 'series', 'description')}
        info['title'] = info['title'] or '未命名'
        for key in ('emotions', 'tools', 'devices'):
            info[key] = tags(fields.get(names[key]))
        record_id = record.get('record_id')
        if not record_id:
            raise RuntimeError('作品缺少记录 ID。')
        result.append((record_id, images[0], info))
    return result


def fetch_published(root, destination, *, check_updates=False):
    config = json.loads((root / 'feishu.json').read_text(encoding='utf-8'))
    secret = os.environ.get('FEISHU_APP_SECRET', '').strip()
    if not secret:
        raise RuntimeError('请在 GitHub Actions Secrets 中设置 FEISHU_APP_SECRET。')
    client = Client(config['appId'], secret)
    node = client.json('/wiki/v2/spaces/get_node', query={'token': config['wikiNodeToken']})['data']['node']
    if node.get('obj_type') != 'bitable' or not node.get('obj_token'):
        raise RuntimeError('配置的知识库节点不是多维表格。')
    app_token = urllib.parse.quote(node['obj_token'], safe='')
    table_id = config['tableId']
    table_path = f'/bitable/v1/apps/{app_token}/tables/{urllib.parse.quote(table_id, safe="")}'
    fields = list(client.items(table_path + '/fields'))
    field_ids = {field['field_name']: field['field_id'] for field in fields}
    for key in ('image', 'status'):
        if config['fields'][key] not in field_ids:
            raise RuntimeError(f'作品库缺少必需字段：{config["fields"][key]}。请补充该列后重试。')
    works = select_published(client.items(table_path + '/records'), config)
    digest = hashlib.sha256(json.dumps(works, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    if check_updates and unchanged(config, digest):
        print('Feishu: published content unchanged; skipped image downloads and deployment.')
        return None
    image_dir = Path(destination) / 'images'
    image_dir.mkdir(parents=True, exist_ok=True)
    meta = {}
    for index, (record_id, image, info) in enumerate(works):
        token = image['file_token']
        extra = {'bitablePerm': {'tableId': table_id, 'attachments': {field_ids[config['fields']['image']]: {record_id: [token]}}}}
        raw = client.request('/drive/v1/medias/' + urllib.parse.quote(token, safe='') + '/download',
                             query={'extra': json.dumps(extra, separators=(',', ':'))}, binary=True)
        # Identify a failing published attachment without logging raw content or credentials.
        label = json.dumps({'title': info['title'], 'file': image.get('name', '未命名附件')}, ensure_ascii=False)
        detected = 'unrecognized'
        if len(raw) >= 12 and raw[4:8] == b'ftyp':
            detected = 'ISO-BMFF/' + raw[8:12].decode('ascii', errors='replace')
        elif raw.lstrip().startswith((b'<', b'<!')):
            detected = 'HTML/XML/SVG'
        try:
            with Image.open(io.BytesIO(raw)) as source:
                detected = source.format or detected
                if detected not in ('JPEG', 'PNG', 'WEBP', 'HEIF'):
                    raise RuntimeError(f'Unsupported published image: {label}; detected={detected}. Use JPG, PNG, WebP or HEIC/HEIF.')
                source.verify()
        except (OSError, ValueError, SyntaxError) as exc:
            raise RuntimeError(
                f'Cannot read published image: {label}; detected={detected}; '
                f'bytes={len(raw)}; decoder={type(exc).__name__}. '
                'Check the attachment format or re-export as JPG/PNG. The live gallery was not changed.'
            ) from None
        name = hashlib.sha256((record_id + ':' + token).encode()).hexdigest()[:24] + '.jpg'
        (image_dir / name).write_bytes(raw)
        info['order'] = index
        meta[name] = info
    print(f'Feishu: prepared {len(meta)} published artworks. Drafts excluded.')
    return image_dir, meta, digest


def unchanged(config, digest):
    # Only a digest of published records is public; no source IDs or draft data.
    url = config.get('publicSiteUrl', '')
    if not url.startswith('https://'):
        return False
    try:
        request = urllib.request.Request(url.rstrip('/') + '/sync-state.json', headers={'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(request, timeout=15) as response:
            state = json.loads(response.read(4096))
        return state.get('digest') == digest
    except (OSError, ValueError):
        # A new site or a temporary connectivity problem should not prevent a build.
        return False
