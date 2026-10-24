from pathlib import Path
import json, shutil, hashlib
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'_site'
if out.exists(): shutil.rmtree(out)
(out/'art').mkdir(parents=True)
site=json.loads((ROOT/'site.json').read_text())
meta=json.loads((ROOT/'artworks.json').read_text())
works=[]
for path in sorted((ROOT/'images').iterdir(),key=lambda p:p.name.casefold()):
    if path.suffix.lower() not in {'.jpg','.jpeg','.png','.webp'}: continue
    key=hashlib.sha256(path.name.encode()).hexdigest()[:16]
    with Image.open(path) as source:
        im=ImageOps.exif_transpose(source).convert('RGB')
        w,h=im.size
        for label,limit,quality in [('thumb',900,86),('full',3000,93)]:
            resized=im.copy(); resized.thumbnail((limit,limit))
            resized.save(out/'art'/f'{key}-{label}.webp',quality=quality)
    info=meta.get(path.name,{})
    works.append(dict(title=info.get('title',path.stem),width=w,height=h,thumb=f'art/{key}-thumb.webp',full=f'art/{key}-full.webp',**{k:info.get(k,'') for k in ['year','medium','size','description']},order=info.get('order',9999)))
works.sort(key=lambda w:w['order'])
for name in ['index.html','style.css','app.js']: shutil.copy(ROOT/name,out/name)
(out/'gallery-data.js').write_text('window.GALLERY='+json.dumps(dict(site=site,works=works),ensure_ascii=False)+';',encoding='utf-8')
print(f'Built {len(works)} artworks into _site')
