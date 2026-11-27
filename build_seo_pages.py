# -*- coding: utf-8 -*-
"""يبني صفحات ثابتة للبحث (قوقل): صفحة لكل قارئ ومصحف وسنة تراويح، وصفحة لكل سورة، وفهرسين، ثم sitemap.xml.

المصادر: lists.json و stations.json و lists/*.m3u و mushaf/meta.json (لا يُعدَّل أي منها).
التشغيل: python build_seo_pages.py   (أعِده بعد أي إضافة للمكتبة أو تعديل في lists.json)
الناتج: reciters.html و surahs.html و reciter/*.html و surah/*.html و sitemap.xml
"""
import json, os, re, html, datetime
from urllib.parse import quote, unquote

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://trtel.vip/'
TODAY = datetime.date.today().isoformat()
J = lambda p: json.load(open(os.path.join(ROOT, p), encoding='utf-8'))
E = lambda s: html.escape(str(s), quote=True)

META = J('mushaf/meta.json')['surahs']          # [عربي، لاتيني، عدد الآيات، الصفحة]
SURAH_AR = [s[0] for s in META]
LISTS, STN = J('lists.json'), J('stations.json')
AR_DIG = str.maketrans('0123456789', '0123456789')


def fmt_d(sec):
    sec = int(sec or 0); h, m = divmod(sec // 60, 60)
    return f'{h}:{m:02d}:{sec % 60:02d}' if h else f'{m}:{sec % 60:02d}'


def surahs_in(title, url):
    """أرقام السور (1..114) في عنوان التلاوة، وإن لم تُعرف فمن رقم الملف."""
    t = re.sub(r'^سورة\s+', '', title.split(' - ')[0]); found = []
    for seg in re.split(r'[،,]\s*', t):
        seg = re.sub(r'^(سورة|سورتا|سور)\s+', '', seg.strip()); best = -1
        for i, n in enumerate(SURAH_AR):
            if seg.startswith(n) and (len(seg) == len(n) or seg[len(n)] in ' ('):
                if best < 0 or len(n) > len(SURAH_AR[best]): best = i
        if best >= 0 and best + 1 not in found: found.append(best + 1)
    if not found:
        m = re.match(r'(\d{3})', unquote(url.rsplit('/', 1)[-1]))
        if m and 1 <= int(m.group(1)) <= 114: found = [int(m.group(1))]
    return found


def read_m3u(path):
    items, d, t = [], 0, ''
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if line.startswith('#EXTINF:'):
            a, _, t = line[8:].partition(','); d = int(float(a or 0))
        elif line.startswith('http'):
            title, _, who = t.rpartition(' - ') if ' - ' in t else (t, '', '')
            items.append({'t': title or t, 'who': who, 'u': line, 'd': d})
    return items


def station_items(m, tar=False):
    sk, out, j = m.get('skip') or [], [], 0
    for n in range(1, 115):
        if n in sk: continue
        out.append({'t': 'سورة ' + SURAH_AR[n - 1], 'u': STN['base'] + m['id'] + '/' + f'{n:03d}%20' + quote(SURAH_AR[n - 1]) + '.mp3',
                    'd': m['d'][j] if j < len(m['d']) else 0, 'who': ''}); j += 1
    return out


# ---------- جمع الصفحات ----------
pages = []   # {slug, name, kind, items, info}
stn_by_id = {m['id']: m for m in STN['mushaf']}
for x in LISTS['mushaf']:
    slug = x['m3u'].rsplit('/', 1)[-1][:-4]
    m = stn_by_id.get(slug)
    if not m: continue
    kind, who = x['name'].split(' - ', 1)
    pages.append({'slug': slug, 'name': x['name'], 'who': who, 'kind': 'mushaf', 'items': station_items(m), 'x': x,
                  'tag': '' if kind == 'المصحف المرتل' else kind,
                  'desc': f'{kind} كاملًا بصوت {who} من المسجد النبوي، 114 سورة'})
for x in LISTS['partial']:
    slug = x['m3u'].rsplit('/', 1)[-1][:-4]
    who = x['name'].split(' - ', 1)[1]
    pages.append({'slug': slug, 'name': 'تسجيلات من مصحف ' + who, 'who': who, 'kind': 'partial', 'x': x,
                  'items': read_m3u(os.path.join(ROOT, 'lists', slug + '.m3u')), 'desc': f'تسجيلات من مصحف {who} في المسجد النبوي'})
for x in LISTS['reciters']:
    slug = x['m3u'].rsplit('/', 1)[-1][:-4]
    nm = x['name']
    pages.append({'slug': slug, 'name': ('تلاوات ' + nm) if nm != 'تلاوات متنوعة' else 'تلاوات متنوعة لقرّاء مختلفين', 'who': nm, 'kind': 'reciter', 'x': x,
                  'items': read_m3u(os.path.join(ROOT, 'lists', slug + '.m3u')), 'desc': f'تلاوات {nm} من صلوات الحرمين وغيرها'})
tar_by_id = {m['id']: m for m in STN['tarawih']}
for x in sorted(LISTS['tarawih'], key=lambda x: -x.get('sort', 0)):
    slug = x['m3u'].rsplit('/', 1)[-1][:-4]
    m = tar_by_id.get(slug)
    if not m: continue
    pages.append({'slug': slug, 'name': x['name'], 'who': '', 'kind': 'tarawih', 'x': x, 'items': station_items(m, True),
                  'desc': f'{x["name"]} كاملة مرتبة بالسور'})

# فهرس السور: كل تسجيل يُنسب إلى كل سورة في عنوانه
by_surah = {n: [] for n in range(1, 115)}
for p in pages:
    for it in p['items']:
        for n in surahs_in(it['t'], it['u']):
            by_surah[n].append((p, it))

# ربط صفحات الشخص الواحد (مصحفه وتلاواته)
norm = lambda s: re.sub(r'^(د\.|الشيخ)\s*', '', s or '').strip()
same = {}
for p in pages:
    if p['who']: same.setdefault(norm(p['who']), []).append(p)

KIND = {'mushaf': 'المصاحف المرتلة', 'partial': 'مصاحف غير مكتملة', 'reciter': 'القرّاء', 'tarawih': 'تراويح المسجد النبوي'}

# ---------- القالب ----------
CSS = """:root{--bg:#f5efe2;--bg2:#fbf6ea;--ink:#22303f;--mut:#7d6f52;--gold:#a8873a;--line:#dccfae;--on:#22303f;--on-ink:#f5efe2;
--display:'Amiri','Traditional Arabic',serif;--body:'IBM Plex Sans Arabic','Segoe UI',Tahoma,sans-serif;color-scheme:light}
:root[data-theme="dark"]{--bg:#0f1a26;--bg2:#17283b;--ink:#e9e2d0;--mut:#8fa3b8;--gold:#c9a35a;--line:#23344a;--on:#c9a35a;--on-ink:#0f1a26;color-scheme:dark}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:400 16px/1.7 var(--body)}
a{color:inherit}.wrap{max-width:860px;margin:0 auto;padding:18px 16px 40px}
header.top{display:flex;align-items:center;gap:12px;justify-content:space-between;border-bottom:1px solid var(--line);padding-bottom:12px}
header.top .brand{display:flex;align-items:center;gap:10px;text-decoration:none;font:700 20px var(--display)}
header.top img{width:40px;height:40px;border-radius:10px}
.live{display:inline-flex;align-items:center;gap:6px;background:var(--on);color:var(--on-ink);text-decoration:none;border-radius:999px;padding:7px 14px;font:500 14px var(--body);white-space:nowrap}
.live:before{content:"";width:8px;height:8px;border-radius:50%;background:#d9534f}
nav.crumb{font-size:13px;color:var(--mut);margin:14px 0 4px}nav.crumb a{color:var(--mut)}
h1{font:700 30px/1.35 var(--display);margin:6px 0 6px}h2{font:700 21px var(--display);margin:26px 0 8px;color:var(--gold)}
p.lead{color:var(--mut);margin:0 0 14px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}.chips a{border:1px solid var(--line);background:var(--bg2);border-radius:999px;padding:4px 12px;text-decoration:none;font-size:14px}
ul.tr{list-style:none;padding:0;margin:0;border:1px solid var(--line);border-radius:14px;background:var(--bg2);overflow:hidden}
ul.tr li{display:flex;align-items:center;gap:10px;padding:9px 12px;border-top:1px solid var(--line)}ul.tr li:first-child{border-top:0}
ul.tr .pl{flex:none;width:34px;height:34px;border-radius:50%;border:0;background:var(--on);color:var(--on-ink);cursor:pointer;display:grid;place-items:center}
ul.tr .pl svg{width:15px;height:15px;fill:currentColor}ul.tr li.on{background:color-mix(in srgb,var(--gold) 12%,transparent)}
ul.tr .t{flex:1;min-width:0}ul.tr .t b{font-weight:500}ul.tr .t small{display:block;color:var(--mut);font-size:13px}
ul.tr .t small a{color:var(--mut)}ul.tr .dl{flex:none;font-size:13px;color:var(--mut)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px}
.grid a{display:block;border:1px solid var(--line);background:var(--bg2);border-radius:12px;padding:8px 10px;text-decoration:none}
.grid a small{display:block;color:var(--mut);font-size:12.5px}
.cols{columns:2 260px;column-gap:16px}.cols a{display:block;break-inside:avoid;padding:6px 0;border-bottom:1px dashed var(--line);text-decoration:none}
.cols a small{color:var(--mut)}
#bar{position:sticky;bottom:0;margin-top:16px;background:var(--bg2);border:1px solid var(--line);border-radius:14px;padding:8px 12px;display:none}
#bar.on{display:block}#bar b{display:block;font-weight:500;font-size:14px}#bar audio{width:100%;height:36px}
footer{margin-top:34px;border-top:1px solid var(--line);padding-top:14px;color:var(--mut);font-size:14px;text-align:center}
footer a{color:var(--mut)}"""

HEAD_JS = "(function(){try{var t=localStorage.getItem('theme');if(t==='dark'||t==='gold')document.documentElement.setAttribute('data-theme','dark');}catch(e){}})();"
PLAY_JS = """(function(){var A='https://archive.org/download/',S='https://files.trtel.vip/a/',bar=document.getElementById('bar'),au=bar.querySelector('audio'),nm=bar.querySelector('b'),cur=null,srv=true;
function go(li){if(cur)cur.classList.remove('on');cur=li;li.classList.add('on');var u=li.dataset.u;nm.textContent=li.querySelector('.t b').textContent;bar.classList.add('on');
au.dataset.u=u;au.dataset.f='';au.src=(srv&&u.indexOf(A)===0)?S+u.slice(A.length):u;au.play().catch(function(){});}
au.addEventListener('error',function(){if(au.dataset.f||!au.dataset.u)return;au.dataset.f='1';srv=false;au.src=au.dataset.u;au.play().catch(function(){});});
au.addEventListener('ended',function(){var n=cur&&cur.nextElementSibling;if(n)go(n);});
document.addEventListener('click',function(e){var b=e.target.closest('.pl');if(!b)return;var li=b.closest('li');if(li===cur&&!au.paused){au.pause();return;}if(li===cur){au.play();return;}go(li);});})();"""
ICON = '<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>'


def page(path, title, desc, h1, crumbs, body, lead='', player=False, extra_ld=None):
    depth = path.count('/'); up = '../' * depth
    url = SITE + path
    ld = [{'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + h}
                                                          for i, (n, h) in enumerate([('ترتيل', '')] + crumbs)]}]
    ld.append({'@type': 'CollectionPage', 'name': title, 'description': desc, 'url': url, 'inLanguage': 'ar',
               'isPartOf': {'@type': 'WebSite', 'name': 'تلاوات من القرآن الكريم', 'url': SITE}})
    if extra_ld: ld += extra_ld
    crumb = ' › '.join([f'<a href="{up or "./"}">ترتيل</a>'] + [f'<a href="{up}{h}">{E(n)}</a>' for n, h in crumbs[:-1]] + [E(crumbs[-1][0])])
    out = f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="ترتيل — تلاوات من القرآن الكريم">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}logo1200.jpg?v=2"><meta property="og:locale" content="ar_AR">
<meta name="twitter:card" content="summary">
<link rel="icon" href="{up}logo512.jpg?v=2">
<meta name="theme-color" content="#f5efe2">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=IBM+Plex+Sans+Arabic:wght@400;500&display=swap" rel="stylesheet">
<script>{HEAD_JS}</script>
<script type="application/ld+json">{json.dumps({'@context': 'https://schema.org', '@graph': ld}, ensure_ascii=False)}</script>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header class="top"><a class="brand" href="{up or './'}"><img src="{up}logo512.jpg?v=2" alt="شعار ترتيل" width="40" height="40">ترتيل</a><a class="live" href="{up or './'}">الإذاعة المباشرة</a></header>
<nav class="crumb" aria-label="مسار الصفحة">{crumb}</nav>
<h1>{E(h1)}</h1>
{f'<p class="lead">{lead}</p>' if lead else ''}
{body}
{'<div id="bar"><b></b><audio controls preload="none"></audio></div>' if player else ''}
<footer><p>هذه الإذاعة وقف لله تعالى، ساهم في نشرها، فالدال على الخير كفاعله.</p>
<p><a href="{up or './'}">الإذاعة المباشرة</a> · <a href="{up}reciters.html">القرّاء والمصاحف</a> · <a href="{up}surahs.html">السور</a> · <a href="{up}mushaf.html">المصحف</a> · <a href="mailto:info@trtel.vip">info@trtel.vip</a></p></footer>
</div>
{f'<script>{PLAY_JS}</script>' if player else ''}
</body>
</html>
"""
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full) or ROOT, exist_ok=True)
    open(full, 'w', encoding='utf-8').write(out)
    return path


def li(it, sub):
    return (f'<li data-u="{E(it["u"])}"><button class="pl" type="button" aria-label="تشغيل">{ICON}</button>'
            f'<span class="t"><b>{E(it["t"])}</b><small>{sub}</small></span>'
            f'<a class="dl" href="{E(it["u"])}" download rel="nofollow">تحميل</a></li>')


def surah_link(n, up):
    return f'<a href="{up}surah/{n}.html">سورة {E(SURAH_AR[n - 1])}</a>'


written = []
# ---------- صفحات القرّاء ----------
for p in pages:
    x, items = p['x'], p['items']
    hrs = x.get('hours') or round(sum(i['d'] for i in items) / 3600, 1)
    rows = []
    for it in items:
        sub = [fmt_d(it['d'])]
        if it['who'] and it['who'] != p['who']: sub.append(E(it['who']))
        ss = surahs_in(it['t'], it['u'])
        if ss: sub.append(' · '.join(surah_link(n, '../') for n in ss[:3]))
        rows.append(li(it, ' · '.join(sub)))
    rel = [q for q in same.get(norm(p['who']), []) if q is not p]
    chips = ''.join(f'<a href="{q["slug"]}.html">{E(q["name"])}</a>' for q in rel)
    links = [f'<a href="{E(x["zip"])}" rel="nofollow">تحميل الكل ZIP ({x.get("mb", "")} MB)</a>' if x.get('zip') else '',
             f'<a href="{E(x["m3u"])}" rel="nofollow">قائمة M3U للتطبيقات</a>' if x.get('m3u') else '',
             f'<a href="{E(x["page"])}" rel="nofollow">الصفحة في الأرشيف</a>' if x.get('page') else '']
    body = (f'<div class="chips">{"".join(l for l in links if l)}{chips}</div>'
            f'<h2>التسجيلات ({len(items)})</h2><ul class="tr">{"".join(rows)}</ul>')
    title = f'{p["name"]} mp3 — استماع وتحميل | ترتيل'
    desc = f'{p["desc"]}: {len(items)} تسجيلًا (نحو {hrs} ساعة) للاستماع المباشر والتحميل mp3 مجانًا، مع إذاعة ترتيل للقرآن الكريم على مدار الساعة.'
    lead = E(f'{p["desc"]}. {len(items)} تسجيلًا، نحو {hrs} ساعة. اضغط ▶ للاستماع هنا، أو حمّل الملف.')
    ld = [{'@type': 'Person', 'name': p['who']}] if p['kind'] != 'tarawih' and p['who'] != 'تلاوات متنوعة' else None
    written.append(page(f'reciter/{p["slug"]}.html', title, desc, p['name'], [('القرّاء والمصاحف', 'reciters.html'), (p['name'], f'reciter/{p["slug"]}.html')],
                        body, lead, player=True, extra_ld=ld))

# ---------- صفحات السور ----------
ORDER = {'mushaf': 0, 'tarawih': 1, 'partial': 2, 'reciter': 3}
for n in range(1, 115):
    ar, en, ay, pg = META[n - 1]
    lst = sorted(by_surah[n], key=lambda pi: ORDER[pi[0]['kind']])
    groups = {}
    for p, it in lst: groups.setdefault(p['kind'], []).append((p, it))
    body = [f'<div class="chips"><a href="../mushaf.html#s={n}&amp;a=1">اقرأ السورة في المصحف مع التفسير</a>'
            + (f'<a href="{n - 1}.html">‹ سورة {E(SURAH_AR[n - 2])}</a>' if n > 1 else '')
            + (f'<a href="{n + 1}.html">سورة {E(SURAH_AR[n])} ›</a>' if n < 114 else '') + '</div>']
    for k in ['mushaf', 'tarawih', 'partial', 'reciter']:
        g = groups.get(k)
        if not g: continue
        rows = []
        for p, it in g:
            who = p['name'] if k == 'tarawih' else (it['who'] if it['who'] and k == 'reciter' and p['who'] == 'تلاوات متنوعة' else p['who'])
            extra = f'{E(it["t"])} · ' if k in ('partial', 'reciter') else ''
            if p.get('tag'): who += f' ({p["tag"]})'
            rows.append(li({**it, 't': who}, f'{extra}{fmt_d(it["d"])} · <a href="../reciter/{p["slug"]}.html">{E(p["name"])}</a>'))
        body.append(f'<h2>{KIND[k]} ({len(g)})</h2><ul class="tr">{"".join(rows)}</ul>')
    cnt = len(lst)
    title = f'سورة {ar} mp3 بصوت أئمة المسجد النبوي والحرمين | ترتيل'
    desc = (f'استمع وحمّل سورة {ar} ({en}) mp3: {cnt} تلاوة من مصاحف أئمة المسجد النبوي وتراويحه وصلوات الحرمين، '
            f'مثل الحذيفي والبدير والمعيقلي والثبيتي والقاسم. آياتها {ay}.')
    lead = E(f'سورة {ar}، رقمها {n} في المصحف، وآياتها {ay}، وتبدأ في الصفحة {pg}. هنا {cnt} تلاوة لها: اضغط ▶ للاستماع أو حمّل الملف.')
    written.append(page(f'surah/{n}.html', title, desc, f'سورة {ar}', [('السور', 'surahs.html'), (f'سورة {ar}', f'surah/{n}.html')],
                        ''.join(body), lead, player=True))

# ---------- الفهرسان ----------
secs = []
for k in ['mushaf', 'partial', 'reciter', 'tarawih']:
    ps = [p for p in pages if p['kind'] == k]
    a = ''.join(f'<a href="reciter/{p["slug"]}.html">{E(p["who"] or p["name"].replace("تراويح المسجد النبوي ", ""))}'
                f'<small>{len(p["items"])} تسجيلًا{(" · " + p["tag"]) if p.get("tag") else ""}</small></a>' for p in ps)
    secs.append(f'<h2>{KIND[k]} ({len(ps)})</h2><div class="grid">{a}</div>')
written.append(page('reciters.html', 'القرّاء ومصاحف المسجد النبوي وتراويحه mp3 — ترتيل',
                    'فهرس القرّاء: المصاحف المرتلة لأئمة المسجد النبوي (الحذيفي، البدير، المعيقلي، الثبيتي، القاسم، الجهني، محمد أيوب وغيرهم)، وتراويح المسجد النبوي من 1411 إلى 1447هـ، وتلاوات الحرمين، للاستماع والتحميل mp3.',
                    'القرّاء والمصاحف', [('القرّاء والمصاحف', 'reciters.html')], ''.join(secs),
                    'كل مصحف وقارئ وسنة تراويح في صفحة مستقلة للاستماع والتحميل. والإذاعة المباشرة تجمعها كلها على مدار الساعة.'))
cols = ''.join(f'<a href="surah/{n}.html">{n}. سورة {E(SURAH_AR[n - 1])} <small>· {len(by_surah[n])} تلاوة</small></a>' for n in range(1, 115))
written.append(page('surahs.html', 'سور القرآن الكريم mp3 بأصوات أئمة المسجد النبوي والحرمين — ترتيل',
                    'فهرس سور القرآن الكريم الـ114: لكل سورة صفحة فيها كل تلاواتها من مصاحف أئمة المسجد النبوي وتراويحه وصلوات الحرمين، للاستماع والتحميل mp3 مجانًا.',
                    'سور القرآن الكريم', [('السور', 'surahs.html')], f'<div class="cols">{cols}</div>',
                    'اختر السورة لتسمعها بأصوات أئمة المسجد النبوي والحرمين، أو تقرأها في المصحف مع التفسير المختصر.'))

# ---------- sitemap ----------
fixed = [('', '1.0', 'weekly'), ('mushaf.html', '0.8', 'monthly'), ('reciters.html', '0.9', 'weekly'), ('surahs.html', '0.9', 'weekly'),
         ('privacy.html', '0.2', 'yearly'), ('terms.html', '0.2', 'yearly')]
urls = fixed + [(w, '0.7', 'monthly') for w in written if w not in ('reciters.html', 'surahs.html')]
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u, pr, cf in urls:
    sm.append(f'  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod><changefreq>{cf}</changefreq><priority>{pr}</priority></url>')
sm.append('</urlset>')
open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write('\n'.join(sm) + '\n')
print(len(written), 'pages;', len(urls), 'urls in sitemap;', sum(len(v) for v in by_surah.values()), 'surah entries')
