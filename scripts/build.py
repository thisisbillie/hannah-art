from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import tempfile
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]


def build(image_dir, meta):
    out = ROOT / '_site'
    if out.exists():
        shutil.rmtree(out)
    (out / 'art').mkdir(parents=True)
    site = json.loads((ROOT / 'site.json').read_text(encoding='utf-8'))
    works = []
    for path in sorted(image_dir.iterdir(), key=lambda p: p.name.casefold()):
        if path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp'}:
            continue
        # Content hash prevents stale browser caches after replacement of a picture.
        key = hashlib.sha256(path.read_bytes()).hexdigest()[:24]
        with Image.open(path) as source:
            im = ImageOps.exif_transpose(source).convert('RGB')
            width, height = im.size
            for label, limit, quality in [('thumb', 900, 86), ('full', 3000, 93)]:
                resized = im.copy()
                resized.thumbnail((limit, limit))
                resized.save(out / 'art' / f'{key}-{label}.webp', quality=quality)
        info = dict(meta.get(path.name, {}))
        if 'series' not in info:
            info['series'] = info.get('category', '')
        list_fields = {}
        for field in ('emotions', 'tools', 'devices'):
            values = info.get(field, [])
            if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
                raise ValueError(f'{path.name}: {field} 必须是字符串列表')
            list_fields[field] = list(dict.fromkeys(value.strip() for value in values if value.strip()))
        works.append(dict(
            title=info.get('title', path.stem), width=width, height=height,
            thumb=f'art/{key}-thumb.webp', full=f'art/{key}-full.webp',
            **{field: info.get(field, '') for field in ['year', 'medium', 'size', 'description', 'series']},
            **list_fields, order=info.get('order', 9999)))
    works.sort(key=lambda work: work['order'])
    for name in ['index.html', 'style.css', 'app.js']:
        shutil.copy(ROOT / name, out / name)
    (out / 'gallery-data.js').write_text(
        'window.GALLERY=' + json.dumps(dict(site=site, works=works), ensure_ascii=False) + ';', encoding='utf-8')
    print(f'Built {len(works)} artworks into _site')


def set_built(value):
    output = os.environ.get('GITHUB_OUTPUT')
    if output:
        with open(output, 'a', encoding='utf-8') as handle:
            handle.write('built=' + str(value).lower() + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--feishu', action='store_true', help='Build only published works from Feishu')
    parser.add_argument('--check-updates', action='store_true', help='Skip unchanged published content')
    args = parser.parse_args()
    if args.feishu:
        from feishu import fetch_published
        # Originals are ephemeral and never copied to _site or committed to Git.
        with tempfile.TemporaryDirectory(prefix='gallery-feishu-') as temp:
            result = fetch_published(ROOT, Path(temp), check_updates=args.check_updates)
            if result is None:
                set_built(False)
                return
            image_dir, meta, digest = result
            build(image_dir, meta)
            (ROOT / '_site' / 'sync-state.json').write_text(json.dumps({'digest': digest}), encoding='utf-8')
    else:
        build(ROOT / 'images', json.loads((ROOT / 'artworks.json').read_text(encoding='utf-8')))
    set_built(True)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from None
