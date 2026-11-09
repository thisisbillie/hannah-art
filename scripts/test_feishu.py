import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import build
import feishu

CONFIG = {
    'appId': 'test-app', 'wikiNodeToken': 'node', 'tableId': 'table', 'publishedValue': '发布',
    'fields': {'title': '作品名', 'image': '画作', 'year': '创作时间', 'emotions': '创作时的情绪',
               'tools': '绘画工具', 'devices': '创作设备', 'medium': '软件或材料',
               'series': '系列', 'description': '创作小记', 'status': '展示状态'}}


def record(status='发布'):
    return {'record_id': 'rec-public', 'fields': {'展示状态': status, '作品名': [{'text': '茶'}],
        '画作': [{'file_token': 'public-image', 'name': '../../outside.jpg'}],
        '创作时的情绪': ['平静', '思念'], '绘画工具': ['手指'], '系列': '茶吧'}}


class FakeClient:
    downloaded = []
    rows = []
    field_names = ['画作', '展示状态']

    def __init__(self, *args):
        pass

    def json(self, *args, **kwargs):
        return {'data': {'node': {'obj_type': 'bitable', 'obj_token': 'base'}}}

    def items(self, path):
        if path.endswith('/fields'):
            return [{'field_name': name, 'field_id': 'field-' + str(index)} for index, name in enumerate(self.field_names)]
        return self.rows

    def request(self, path, **kwargs):
        self.downloaded.append(path)
        out = io.BytesIO()
        Image.new('RGB', (40, 60), 'red').save(out, 'PNG')
        return out.getvalue()


class SyncTests(unittest.TestCase):
    def test_drafts_not_mapped_or_downloaded(self):
        draft = {'record_id': 'private', 'fields': {'展示状态': '草稿', '创作小记': {'invalid': 'private'}, '画作': 'invalid'}}
        self.assertEqual(len(feishu.select_published([draft, record()], CONFIG)), 1)
        self.assertEqual(feishu.select_published([record(''), record('已发布')], CONFIG), [])

    def test_invalid_published_image_stops_sync(self):
        item = record()
        item['fields']['画作'] = []
        with self.assertRaisesRegex(RuntimeError, '缺少画作'):
            feishu.select_published([item], CONFIG)

    def test_multiselect_and_rich_text(self):
        work = feishu.select_published([record()], CONFIG)[0][2]
        self.assertEqual(work['title'], '茶')
        self.assertEqual(work['emotions'], ['平静', '思念'])
        self.assertEqual(work['tools'], ['手指'])
        with self.assertRaises(RuntimeError):
            feishu.tags('平静')

    def test_pagination(self):
        client = object.__new__(feishu.Client)
        pages = iter([{'data': {'items': [1], 'has_more': True, 'page_token': 'next'}},
                      {'data': {'items': [2], 'has_more': False}}])
        client.json = lambda *args, **kwargs: next(pages)
        self.assertEqual(list(client.items('/records')), [1, 2])
        client.json = lambda *args, **kwargs: {'data': {'items': [], 'has_more': True}}
        with self.assertRaises(RuntimeError):
            list(client.items('/records'))

    def test_sync_and_build_publish_only_and_strip_original_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'feishu.json').write_text(json.dumps(CONFIG))
            (root / 'site.json').write_text(json.dumps({'name': '河边草'}))
            for name in ['index.html', 'style.css', 'app.js']:
                (root / name).write_text('test')
            FakeClient.rows = [record(), {'fields': {'展示状态': '草稿', '创作小记': 'PRIVATE-NOTE'}}]
            FakeClient.downloaded = []
            with patch.dict('os.environ', {'FEISHU_APP_SECRET': 'SECRET-MARKER'}), patch.object(feishu, 'Client', FakeClient):
                images, meta, digest = feishu.fetch_published(root, root / 'temporary')
                self.assertEqual(len(FakeClient.downloaded), 1)
                self.assertEqual(len(list(images.iterdir())), 1)
                self.assertTrue(all(p.parent == images for p in images.iterdir()))
                with patch.object(build, 'ROOT', root):
                    build.build(images, meta)
                output = (root / '_site/gallery-data.js').read_text()
                self.assertNotIn('PRIVATE-NOTE', output)
                self.assertNotIn('SECRET-MARKER', output)
                self.assertNotIn('public-image', output)
                self.assertIn('手指', output)
                self.assertEqual(len(list((root / '_site/art').iterdir())), 2)
                with patch.object(feishu, 'unchanged', return_value=True):
                    self.assertIsNone(feishu.fetch_published(root, root / 'skipped', check_updates=True))
                self.assertEqual(len(FakeClient.downloaded), 1)
                with patch.object(FakeClient, 'field_names', ['画作']):
                    with self.assertRaisesRegex(RuntimeError, '展示状态'):
                        feishu.fetch_published(root, root / 'missing')

    def test_heic_attachment_builds_webp(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'feishu.json').write_text(json.dumps(CONFIG))
            (root / 'site.json').write_text(json.dumps({'name': 'HEIC test'}))
            for name in ['index.html', 'style.css', 'app.js']:
                (root / name).write_text('test')
            photo = Image.new('RGB', (80, 120), 'blue')
            out = io.BytesIO()
            photo.save(out, format='HEIF', quality=90)
            heic = out.getvalue()
            self.assertEqual(heic[4:8], b'ftyp')
            row = record()
            row['fields']['画作'][0]['name'] = 'IMG_5679.HEIC'
            FakeClient.rows = [row]
            with patch.dict('os.environ', {'FEISHU_APP_SECRET': 'test-secret'}), patch.object(feishu, 'Client', FakeClient):
                with patch.object(FakeClient, 'request', return_value=heic):
                    images, meta, _ = feishu.fetch_published(root, root / 'temp')
                with patch.object(build, 'ROOT', root):
                    build.build(images, meta)
            data = json.loads((root / '_site/gallery-data.js').read_text()[15:-1])
            self.assertEqual(len(data['works']), 1)
            self.assertEqual((data['works'][0]['width'], data['works'][0]['height']), (80, 120))
            for path in (root / '_site/art').iterdir():
                with Image.open(path) as image:
                    image.load()
                    self.assertEqual(image.format, 'WEBP')

    def test_invalid_attachment_identifies_work_without_logging_payload(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'feishu.json').write_text(json.dumps(CONFIG))
            FakeClient.rows = [record()]
            with patch.dict('os.environ', {'FEISHU_APP_SECRET': 'test-secret'}), patch.object(feishu, 'Client', FakeClient):
                with patch.object(FakeClient, 'request', return_value=b'private-invalid-payload'):
                    with self.assertRaises(RuntimeError) as error:
                        feishu.fetch_published(root, root / 'temp')
            self.assertIn('茶', str(error.exception))
            self.assertNotIn('private-invalid-payload', str(error.exception))

    def test_auth_error_never_echoes_response_credentials(self):
        class Response(io.BytesIO):
            headers = {'Content-Type': 'application/json'}
        client = object.__new__(feishu.Client)
        client.token = None
        class Opener:
            def open(self, *args, **kwargs):
                return Response(b'{"code":99991663,"msg":"SECRET-MARKER"}')
        client.opener = Opener()
        with self.assertRaises(RuntimeError) as error:
            client.json('/auth', payload={'app_secret': 'SECRET-MARKER'})
        self.assertNotIn('SECRET-MARKER', str(error.exception))


if __name__ == '__main__':
    unittest.main()
