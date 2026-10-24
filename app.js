const data=window.GALLERY||{site:{name:'作品集',bio:''},works:[]};
const $=id=>document.getElementById(id);document.title=data.site.name; $('name').textContent=data.site.name;$('bio').textContent=data.site.bio||'';const holder=data.site.copyrightHolder||data.site.name;
const rights=data.site.rights||'保留所有权利。';
$('footer').textContent=`画作 © ${new Date().getFullYear()} ${holder}。${rights}`;
if(data.site.rightsEnglish){const en=document.createElement('div');en.lang='en';en.textContent=data.site.rightsEnglish;$('footer').append(en)}
const credit=document.createElement('p');credit.className='artwork-credit';credit.textContent=`© ${holder} · ${rights}`;$('original').after(credit);
 $('aboutButton').hidden=!data.site.bio;
let current=0,request=0;let visible=data.works;
const filters=document.createElement('div');filters.className='filters';filters.setAttribute('role','group');filters.setAttribute('aria-label','分类');
const label=document.createElement('span');label.textContent='分类 /';filters.append(label);$('gallery').before(filters);
const categories=[...new Set(data.works.map(w=>w.category).filter(Boolean))];
const options=[{label:'全部',value:null},...categories.map(c=>({label:c,value:c}))];
if(categories.length&&data.works.some(w=>!w.category))options.push({label:'未分类',value:''});
function selectCategory(value){visible=value===null?data.works:data.works.filter(w=>(w.category||'')===value);for(const b of filters.querySelectorAll('button'))b.setAttribute('aria-pressed',String(b.categoryValue===value));render();}
for(const option of options){const b=document.createElement('button');b.type='button';b.textContent=option.label;b.categoryValue=option.value;b.setAttribute('aria-pressed',String(option.value===null));b.onclick=()=>selectCategory(option.value);filters.append(b)}
const viewer=$('viewer');
function render(){$('gallery').replaceChildren();visible.forEach((w,i)=>{const f=document.createElement('figure');f.className='art';const b=document.createElement('button');b.setAttribute('aria-label',`查看：${w.title}`);const frame=document.createElement('div');frame.className='frame';const img=new Image();img.src=w.thumb;img.alt=w.title;img.width=w.width;img.height=w.height;img.loading=i<3?'eager':'lazy';img.decoding='async';img.onerror=()=>{img.alt='图片暂时无法加载';};frame.append(img);b.append(frame);b.onclick=()=>{viewer.showModal();document.body.classList.add('modal');show(i)};const c=document.createElement('figcaption');const n=document.createElement('small');n.textContent=String(i+1).padStart(2,'0');c.append(n,document.createTextNode(w.title));f.append(b,c);$('gallery').append(f)});$('empty').hidden=!!visible.length;}render();
function show(i){if(!visible.length)return;current=(i+visible.length)%visible.length;const w=visible[current],token=++request;$('large').src=w.thumb;$('large').alt=w.title;$('title').textContent=w.title;$('details').textContent=[w.year,w.medium,w.size,w.description].filter(Boolean).join(' · ');$('count').textContent=`${current+1} / ${visible.length}`;$('original').href=w.full;$('loading').textContent='正在加载高清图…';const full=new Image();full.onload=()=>{if(token===request){$('large').src=w.full;$('loading').textContent=''}};full.onerror=()=>{if(token===request)$('loading').textContent='高清图加载失败，可点击下方链接重试'};full.src=w.full;}
$('close').onclick=()=>viewer.close();viewer.addEventListener('close',()=>{request++;document.body.classList.remove('modal')});$('prev').onclick=()=>show(current-1);$('next').onclick=()=>show(current+1);document.addEventListener('keydown',e=>{if(viewer.open&&['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();show(current+(e.key==='ArrowRight'?1:-1))}});$('aboutButton').onclick=()=>$('about').showModal();$('closeAbout').onclick=()=>$('about').close();
