# -*- coding: utf-8 -*-
"""يبني صفحات البحث (قوقل) بكل اللغات: صفحة لكل قارئ ومصحف وسنة تراويح، وصفحة لكل سورة، وفهرسين، ونسخة من الموقع والمصحف لكل لغة، ثم خرائط الموقع.

المصادر: lists.json و stations.json و lists/*.m3u و mushaf/meta.json (لا يُعدَّل أي منها)، ونصوص اللغات i18n/src/<code>.json.
التشغيل: python build_seo_pages.py   (أعِده بعد أي إضافة للمكتبة أو تعديل في lists.json أو index.html أو mushaf.html أو نصوص لغة)
الناتج (العربية في الجذر، وكل لغة في مجلدها /<code>/):
  reciters.html و surahs.html و reciter/*.html و surah/*.html، ومثلها في <code>/، و<code>/index.html و<code>/mushaf.html
  i18n/<code>.js (نصوص الواجهة)، وروابط hreflang وقائمة اللغات داخل index.html و mushaf.html
  sitemap.xml (فهرس) و sitemap-<code>.xml لكل لغة
إضافة لغة: ضع i18n/src/<code>.json (انسخ en.json وترجمه بالمعنى) ثم أعد التشغيل. لا يُترجم القرآن ولا التفسير هنا: ترجمات المعاني من QuranEnc في mushaf/tr/.
"""
import json, os, re, html, datetime, glob, hashlib
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
    pages.append({'slug': slug, 'name': x['name'], 'who': who, 'kind': 'mushaf', 'kindw': kind, 'items': station_items(m), 'x': x,
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


# ---------- اللغات ----------
SRC = os.path.join(ROOT, 'i18n', 'src')
NAMES = J('i18n/src/_names.json')            # أسماء السور والقرّاء بالحروف اللاتينية (للغات التي لا اسم لها في QuranEnc)
# بيانات ترجمات المعاني من مستودع quran-tr: نسخة محلية بجانب هذا المستودع إن وُجدت، وإلا من الموقع المنشور
def TRJ(name):
    for d in (os.environ.get('QURAN_TR', ''), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'quran-tr')):
        if d and os.path.exists(os.path.join(d, name)): return json.load(open(os.path.join(d, name), encoding='utf-8'))
    import urllib.request
    return json.load(urllib.request.urlopen('https://trtel.vip/quran-tr/' + name, timeout=60))
def TRF(key, n):
    """آيات سورة n من ترجمة key (نص، أو [نص، حواشٍ])."""
    return TRJ(f'{key}/{n}.json')
QTEXT = J('mushaf/search.json')['q']             # نص المصحف بالرسم العثماني (مجمع الملك فهد) لكل سورة
SOWAR = TRJ('sowar.json')       # أسماء السور الرسمية بكل لغة من QuranEnc
TRSEL = TRJ('select.json')      # ترجمة المعاني المعتمدة لكل لغة
TRIDX = TRJ('index.json')       # الترجمات المحفوظة

# نصوص العربية (الأصل): نفس مفاتيح قسم p في ملفات اللغات
AR = {
    'qTitle': '{s} مكتوبة كاملة بالرسم العثماني مع تفسيرها | ترتيل',
    'qDesc': 'اقرأ {s} مكتوبة كاملة ({ay} آية) بالرسم العثماني من مصحف المدينة، مع تفسيرها من المختصر في تفسير القرآن الكريم، واستمع إلى تلاواتها.',
    'qH1': '{s} مكتوبة مع تفسيرها', 'qLead': 'السورة رقم {no} في المصحف، وعدد آياتها {ay}، وتبدأ في الصفحة {pg}.',
    'qListen': 'استمع إلى تلاواتها', 'qText': 'نص السورة مع تفسيرها', 'qSrc': 'التفسير: المختصر في تفسير القرآن الكريم، مركز تفسير للدراسات القرآنية.', 'qNote': '',
    'brand': 'ترتيل', 'siteName': 'ترتيل — تلاوات من القرآن الكريم', 'live': 'الإذاعة المباشرة', 'crumbL': 'مسار الصفحة', 'logoAlt': 'شعار ترتيل',
    'navRec': 'القرّاء والمصاحف', 'navSur': 'السور', 'navMus': 'المصحف', 'play': 'تشغيل', 'dl': 'تحميل',
    'surahX': 'سورة {s}', 'zipAll': 'تحميل الكل ZIP ({mb} MB)', 'm3u': 'قائمة M3U للتطبيقات', 'arch': 'الصفحة في الأرشيف',
    'recs': 'التسجيلات ({n})', 'nRec': '{n} تسجيلًا', 'nTil': '{n} تلاوة',
    'recTitle': '{name} mp3 — استماع وتحميل | ترتيل',
    'recDesc': '{desc}: {n} تسجيلًا (نحو {h} ساعة) للاستماع المباشر والتحميل mp3 مجانًا، مع إذاعة ترتيل للقرآن الكريم على مدار الساعة.',
    'recLead': '{desc}. {n} تسجيلًا، نحو {h} ساعة. اضغط ▶ للاستماع هنا، أو حمّل الملف.',
    'kMushaf': 'المصاحف المرتلة', 'kPartial': 'مصاحف غير مكتملة', 'kReciter': 'القرّاء', 'kTarawih': 'تراويح المسجد النبوي',
    'readMushaf': 'اقرأ السورة في المصحف مع التفسير',
    'surTitle': 'سورة {s} mp3 بصوت أئمة المسجد النبوي والحرمين | ترتيل',
    'surDesc': 'استمع وحمّل سورة {s} ({en}) mp3: {n} تلاوة من مصاحف أئمة المسجد النبوي وتراويحه وصلوات الحرمين، مثل الحذيفي والبدير والمعيقلي والثبيتي والقاسم. آياتها {ay}.',
    'surLead': 'سورة {s}، رقمها {no} في المصحف، وآياتها {ay}، وتبدأ في الصفحة {pg}. هنا {n} تلاوة لها: اضغط ▶ للاستماع أو حمّل الملف.',
    'recsTitle': 'القرّاء ومصاحف المسجد النبوي وتراويحه mp3 — ترتيل',
    'recsDesc': 'فهرس القرّاء: المصاحف المرتلة لأئمة المسجد النبوي (الحذيفي، البدير، المعيقلي، الثبيتي، القاسم، الجهني، محمد أيوب وغيرهم)، وتراويح المسجد النبوي من 1411 إلى 1447هـ، وتلاوات الحرمين، للاستماع والتحميل mp3.',
    'recsH1': 'القرّاء والمصاحف',
    'recsLead': 'كل مصحف وقارئ وسنة تراويح في صفحة مستقلة للاستماع والتحميل. والإذاعة المباشرة تجمعها كلها على مدار الساعة.',
    'sursTitle': 'سور القرآن الكريم mp3 بأصوات أئمة المسجد النبوي والحرمين — ترتيل',
    'sursDesc': 'فهرس سور القرآن الكريم الـ114: لكل سورة صفحة فيها كل تلاواتها من مصاحف أئمة المسجد النبوي وتراويحه وصلوات الحرمين، للاستماع والتحميل mp3 مجانًا.',
    'sursH1': 'سور القرآن الكريم',
    'sursLead': 'اختر السورة لتسمعها بأصوات أئمة المسجد النبوي والحرمين، أو تقرأها في المصحف مع التفسير المختصر.',
    'waqf': 'هذه الإذاعة وقف لله تعالى، ساهم في نشرها، فالدال على الخير كفاعله.', 'langs': 'اللغات',
}
ARABIC_SCRIPT = {'arabic'}   # لغات تُكتب بالحرف العربي: تبقى أسماء القرّاء كما هي


def load_langs():
    out = {}
    for f in sorted(glob.glob(os.path.join(SRC, '*.json'))):
        code = os.path.basename(f)[:-5]
        if code.startswith('_'): continue
        L = json.load(open(f, encoding='utf-8')); L['code'] = code
        en = out.get('en') or json.load(open(os.path.join(SRC, 'en.json'), encoding='utf-8'))
        for sec in ('t', 'm', 'x', 'p'):          # ما لم يُترجم بعد يظهر بالإنجليزية بدل مفتاح فارغ
            L[sec] = {**en[sec], **L.get(sec, {})}
        names = SOWAR.get(L.get('sowar', code)) if L.get('sowar', code) else None
        s = list(names) if names and len(names) == 114 and not L.get('latinSurahs') else list(NAMES['surahs_latin'])
        s = [re.sub(r'\s*-\s+', '-', re.sub(r'\s+', ' ', x)).strip() for x in s]     # تنظيف مسافات زائدة في بعض القوائم
        s = [x.title() if sum(c.isupper() for c in x) > sum(c.islower() for c in x) else x for x in s]   # أسماء مكتوبة بحروف كبيرة كلها (hr, mk, ro)
        s = [re.sub(r"^S[ûu]r[ae]tu(?:'[a-zş]-|\s+)", '', x) for x in s] if code == 'tr' else s       # «Sûretu'l-Haşr» → «Haşr» لأن كلمة «Sure» تُضاف قبله
        for k, v in (L.get('s_fix') or {}).items(): s[int(k) - 1] = v
        L['s'] = s
        L['t'].setdefault('fatiha', s[0]) if 'fatiha' in json.load(open(f, encoding='utf-8')).get('t', {}) else L['t'].update(fatiha=s[0], nas=s[113])
        L.setdefault('qe', code if code in SOWAR else 'en')
        L['rec'] = {} if L.get('script') in ARABIC_SCRIPT else {**NAMES['reciters_latin'], **(L.get('rec') or {})}
        if L.get('script') in ARABIC_SCRIPT: L['rec'] = dict(L.get('rec') or {})
        sel = TRSEL.get(L.get('trLang', code), {})
        L['tr'] = sel.get('tr') if sel.get('tr') in TRIDX else None
        L['tf'] = sel.get('tf') if sel.get('tf') in TRIDX else None
        out[code] = L
    return {'en': out['en'], **{k: v for k, v in out.items() if k != 'en'}} if 'en' in out else out


LANGS = load_langs()
LANG_LIST = [[c, L['name'], L['dir']] for c, L in LANGS.items()]
# لغات بلا واجهة مترجمة: تفتح بواجهة لغة بلدها الرسمية (base) مع ترجمة معانيها، ولا صفحات مستقلة لها (حتى لا تتكرر الصفحات في البحث)
FALLBACK = {k: v for k, v in J('i18n/src/_fallback.json').items() if not k.startswith('_') and k not in LANGS and (v['base'] in LANGS or v['base'] == 'ar')}
for c, v in FALLBACK.items():
    sel = TRSEL.get(c, {})
    LANG_LIST.append([c, v['name'], v['dir'], v['base'], sel.get('tr') if sel.get('tr') in TRIDX else '', sel.get('tf') if sel.get('tf') in TRIDX else ''])
ALL = ['ar'] + list(LANGS)
SRE = re.compile('(^|[\\s،(])(' + '|'.join(sorted(map(re.escape, SURAH_AR), key=len, reverse=True)) + ')(?=$|[\\s،)])')


class Ctx:
    """سياق لغة واحدة: النصوص ودوال ترجمة العناوين والأسماء (نفس منطق trTitle و trRec في index.html)."""
    def __init__(self, code):
        self.code, self.L = code, LANGS.get(code)
        self.ar = code == 'ar'
        self.P = AR if self.ar else {**self.L['p'], 'waqf': self.L['t']['waqf'], 'langs': self.L['t']['langs']}
        self.dir = 'rtl' if self.ar else self.L['dir']
        self.pre = '' if self.ar else code + '/'
        self.snames = SURAH_AR if self.ar else self.L['s']
        self.rec_keys = [] if self.ar else sorted(self.L['rec'], key=len, reverse=True)

    def t(self, k, **kw):
        s = self.P[k]
        for a, b in kw.items(): s = s.replace('{' + a + '}', str(b))
        return s

    def title(self, t):
        if self.ar: return t
        X = self.L['x']
        t = re.sub(r'^(?:سورة\s+)?من\s+(.+?)\s+إلى\s+', lambda m: m.group(1) + ' – ', t)      # «من كذا إلى كذا» ← «كذا – كذا»
        if '{s}' in X['surah']:   # لغات يأتي فيها اسم السورة قبل كلمة «سورة» (مثل «{s}章»)
            t = re.sub(r'^سورة\s+(' + SRE.pattern.split(')(', 1)[1].split(')(?=', 1)[0] + ')', lambda m: X['surah'].replace('{s}', m.group(1)), t)
        else:
            t = re.sub(r'^سورة\s+', lambda m: X['surah'], t)
        t = SRE.sub(lambda m: (X['comma'] if m.group(1) == '،' else m.group(1)) + self.snames[SURAH_AR.index(m.group(2))], t)
        t = t.replace('،', X['comma'])
        t = re.sub(r'(\d+)هـ', lambda m: X['ah'].replace('$1', m.group(1)), t)
        t = re.sub(r'مختارات من (\d+) سورة - أولها', lambda m: X['sel'].replace('$1', m.group(1)), t)
        for a, b in (('تراويح المسجد النبوي', 'tarawih'), ('المصحف المرتل', 'recited'), ('مصحف الحرمين', 'haramain'), ('مصحف غير مكتمل', 'incomplete')):
            t = t.replace(a, X[b])
        for a in self.rec_keys: t = t.replace(a, self.L['rec'][a])
        return t

    def who(self, r):
        if self.ar or not r: return r
        if r == 'تلاوات متنوعة': return self.P['whoVarious']
        X, rec = self.L['x'], self.L['rec']
        out = (X['comma'] + ' ').join(rec.get(n, n) for n in r.split('، '))
        return out if out != r else self.title(r)

    def surah(self, n): return self.t('surahX', s=self.snames[n - 1])

    def kindw(self, k): return k if self.ar else self.L['x']['haramain' if k == 'مصحف الحرمين' else 'recited']

    def name(self, p):
        if self.ar: return p['name']
        k = p['kind']
        if k == 'mushaf': return self.kindw(p['kindw']) + ' - ' + self.who(p['who'])
        if k == 'partial': return self.t('namePartial', who=self.who(p['who']))
        if k == 'reciter': return self.P['nameVarious'] if p['who'] == 'تلاوات متنوعة' else self.t('nameReciter', who=self.who(p['who']))
        return self.title(p['name'])

    def desc(self, p):
        if self.ar: return p['desc']
        k = p['kind']
        if k == 'mushaf': return self.t('descMushaf', kind=self.kindw(p['kindw']), who=self.who(p['who']))
        if k == 'partial': return self.t('descPartial', who=self.who(p['who']))
        if k == 'reciter': return self.P['nameVarious'] if p['who'] == 'تلاوات متنوعة' else self.t('descReciter', who=self.who(p['who']))
        return self.t('descTarawih', name=self.title(p['name']))


# ---------- القالب ----------
ind = lambda n: ''.join('٠١٢٣٤٥٦٧٨٩'[int(d)] for d in str(n))   # أرقام الآيات: خط حفص يرسمها علامة آية
QCSS = ("@font-face{font-family:Hafs;src:url(FONT) format('truetype');font-display:swap}"
        ".ay{border-bottom:1px solid var(--line);padding:14px 0}.q{font:28px/2.1 Hafs,Amiri,serif;direction:rtl;text-align:right;margin:0 0 6px;color:var(--ink)}.q:empty{min-height:1em}"
        ".bsm{text-align:center;margin:14px 0}.tx{margin:0;line-height:1.75}.tx b{color:var(--gold)}.fn{font-size:13px;color:var(--mut);white-space:pre-line;margin:6px 0 0}"
        ".qw{font-weight:700;color:var(--gold)}.src{font-size:13px;color:var(--mut);margin:16px 0}@media(max-width:480px){.q{font-size:24px}}")
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

CSS += """
.lg{margin:14px 0 0}.lg summary{cursor:pointer;display:inline-flex;align-items:center;gap:6px;list-style:none}.lg summary::-webkit-details-marker{display:none}
.lg summary svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:1.6}
.lg div{display:flex;flex-wrap:wrap;gap:6px 12px;justify-content:center;margin-top:10px}.lg a{text-decoration:none}.lg a[aria-current]{color:var(--ink);font-weight:600}
html:not([lang="ar"]) h1,html:not([lang="ar"]) h2,html:not([lang="ar"]) header.top .brand{font-family:var(--body),system-ui,sans-serif}
html:not([lang="ar"]) h1{font-size:26px}html:not([lang="ar"]) h2{font-size:19px}"""

HEAD_JS = "(function(){try{var t=localStorage.getItem('theme');if(t==='dark'||t==='gold')document.documentElement.setAttribute('data-theme','dark');}catch(e){}})();"
PLAY_JS = """(function(){var A='https://archive.org/download/',S='https://files.trtel.vip/a/',bar=document.getElementById('bar'),au=bar.querySelector('audio'),nm=bar.querySelector('b'),cur=null,srv=true;
function go(li){if(cur)cur.classList.remove('on');cur=li;li.classList.add('on');var u=li.dataset.u;nm.textContent=li.querySelector('.t b').textContent;bar.classList.add('on');
au.dataset.u=u;au.dataset.f='';au.src=(srv&&u.indexOf(A)===0)?S+u.slice(A.length):u;au.play().catch(function(){});}
au.addEventListener('error',function(){if(au.dataset.f||!au.dataset.u)return;au.dataset.f='1';srv=false;au.src=au.dataset.u;au.play().catch(function(){});});
au.addEventListener('ended',function(){var n=cur&&cur.nextElementSibling;if(n)go(n);});
document.addEventListener('click',function(e){var b=e.target.closest('.pl');if(!b)return;var li=b.closest('li');if(li===cur&&!au.paused){au.pause();return;}if(li===cur){au.play();return;}go(li);});})();"""
ICON = '<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>'
GLOBE = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.6 2.4 3.9 5.4 3.9 9s-1.3 6.6-3.9 9c-2.6-2.4-3.9-5.4-3.9-9S9.4 5.4 12 3z"/></svg>'
OG_LOCALE = {'ar': 'ar_AR'}


def lang_redirect_js():
    """من اختار لغة تبقى له، وأول زيارة تتبع لغة الجهاز (نفس منطق index.html). يُضاف لصفحات العربية فقط."""
    s = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    i = s.index('(function(){try{if(window.TRL)return;'); j = s.index('}catch(e){}})();', i) + len('}catch(e){}})();')
    return 'window.TRLANGS=' + json.dumps(LANG_LIST, ensure_ascii=False, separators=(',', ':')) + ';' + s[i:j].replace('\n', '')


def alternates(path):
    """روابط hreflang المتبادلة لصفحة مسارها بالعربية path."""
    out = [f'<link rel="alternate" hreflang="ar" href="{SITE}{path}">']
    out += [f'<link rel="alternate" hreflang="{c}" href="{SITE}{c}/{path}">' for c in LANGS]
    out.append(f'<link rel="alternate" hreflang="x-default" href="{SITE}{path}">')
    return ''.join(out)


def lang_links(C, path, up):
    if not LANGS: return ''
    items = [['ar', 'العربية', 'rtl']] + LANG_LIST
    a = ''.join(f'<a href="{up}{"" if (x[3] if len(x) > 3 else x[0]) == "ar" else (x[3] if len(x) > 3 else x[0]) + "/"}{path}" lang="{x[0]}"'
                f'{"" if len(x) > 3 else f" hreflang=\"{x[0]}\""} data-i="{i}"{" aria-current=\"true\"" if x[0] == C.code else ""}>{E(x[1])}</a>'
                for i, x in enumerate(items))
    return f'<details class="lg"><summary>{GLOBE}{E(C.P["langs"])}</summary><div>{a}</div></details><script src="{up}lg.js?v={SHARED["lg.js"]}" defer></script>'


def shared_files():
    """ملفات مشتركة بين كل الصفحات (بدل تكرارها في آلاف الصفحات): seo.css وlg.js، وتُرجع بصمة كل منهما للروابط."""
    items = [['ar', 'العربية', 'rtl']] + LANG_LIST
    files = {'seo.css': CSS + QCSS.replace('FONT', 'mushaf/uthmanic_hafs_v22.ttf'),
             'lg.js': "(function(){var A=" + json.dumps(items, ensure_ascii=False, separators=(',', ':')) + ";document.querySelector('.lg').addEventListener('click',function(e){var a=e.target.closest('a');if(!a)return;"
                      "var x=A[+a.dataset.i],S=localStorage;try{S.setItem('lang',x[3]||x[0]);if(x[3]){S.setItem('lang2',x[0]);x[4]?S.setItem('mushaf:tr',x[4]):S.removeItem('mushaf:tr');x[5]?S.setItem('mushaf:tf',x[5]):S.removeItem('mushaf:tf');}"
                      "else{S.removeItem('lang2');S.removeItem('mushaf:tr');S.removeItem('mushaf:tf');}}catch(z){}});})();\n"}
    out = {}
    for n, c in files.items():
        open(os.path.join(ROOT, n), 'w', encoding='utf-8').write(c)
        out[n] = hashlib.md5(c.encode()).hexdigest()[:8]
    return out


def page(C, path, title, desc, h1, crumbs, body, lead='', player=False, extra_ld=None, quran=False):
    P = C.P
    depth = path.count('/'); up = '../' * depth          # إلى جذر اللغة
    rup = up + ('' if C.ar else '../')                    # إلى جذر الموقع (الملفات المشتركة)
    base = SITE + C.pre; url = base + path
    ld = [{'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': base + h}
                                                          for i, (n, h) in enumerate([(P['brand'], '')] + crumbs)]}]
    ld.append({'@type': 'CollectionPage', 'name': title, 'description': desc, 'url': url, 'inLanguage': C.code,
               'isPartOf': {'@type': 'WebSite', 'name': 'تلاوات من القرآن الكريم' if C.ar else P['siteName'], 'url': base}})
    if extra_ld: ld += extra_ld
    crumb = ' › '.join([f'<a href="{up or "./"}">{E(P["brand"])}</a>'] + [f'<a href="{up}{h}">{E(n)}</a>' for n, h in crumbs[:-1]] + [E(crumbs[-1][0])])
    out = f"""<!doctype html>
<html lang="{C.code}" dir="{C.dir}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}">
{alternates(path)}
<meta property="og:type" content="website"><meta property="og:site_name" content="{E(P['siteName'])}">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}logo1200.jpg?v=2"><meta property="og:locale" content="{'ar_AR' if C.ar else C.L['loc'].replace('-', '_')}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="{rup}logo512.jpg?v=2">
<meta name="theme-color" content="#f5efe2">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=IBM+Plex+Sans+Arabic:wght@400;500&display=swap" rel="stylesheet">
<script>{HEAD_JS}{('window.TRUP=' + str(depth) + ';' + REDIR) if C.ar and REDIR else ''}</script>
<script type="application/ld+json">{json.dumps({'@context': 'https://schema.org', '@graph': ld}, ensure_ascii=False)}</script>
<link rel="stylesheet" href="{rup}seo.css?v={SHARED['seo.css']}">
</head>
<body>
<div class="wrap">
<header class="top"><a class="brand" href="{up or './'}"><img src="{rup}logo512.jpg?v=2" alt="{E(P['logoAlt'])}" width="40" height="40">{E(P['brand'])}</a><a class="live" href="{up or './'}">{E(P['live'])}</a></header>
<nav class="crumb" aria-label="{E(P['crumbL'])}">{crumb}</nav>
<h1>{E(h1)}</h1>
{f'<p class="lead">{lead}</p>' if lead else ''}
{body}
{'<div id="bar"><b></b><audio controls preload="none"></audio></div>' if player else ''}
<footer><p>{E(P['waqf'])}</p>
<p><a href="{up or './'}">{E(P['live'])}</a> · <a href="{up}reciters.html">{E(P['navRec'])}</a> · <a href="{up}surahs.html">{E(P['navSur'])}</a> · <a href="{up}mushaf.html">{E(P['navMus'])}</a> · <a href="mailto:info@trtel.vip">info@trtel.vip</a></p>
{lang_links(C, path, rup)}</footer>
</div>
{f'<script>{PLAY_JS}</script>' if player else ''}
</body>
</html>
"""
    full = os.path.join(ROOT, C.pre + path)
    os.makedirs(os.path.dirname(full) or ROOT, exist_ok=True)
    open(full, 'w', encoding='utf-8').write(out)
    return path


def build_pages(C):
    P, T = C.P, C.title
    def li(it, sub, t=None):
        return (f'<li data-u="{E(it["u"])}"><button class="pl" type="button" aria-label="{E(P["play"])}">{ICON}</button>'
                f'<span class="t"><b>{E(t if t is not None else T(it["t"]))}</b><small>{sub}</small></span>'
                f'<a class="dl" href="{E(it["u"])}" download rel="nofollow">{E(P["dl"])}</a></li>')
    surah_link = lambda n, up: f'<a href="{up}surah/{n}.html">{E(C.surah(n))}</a>'
    KIND = {'mushaf': P['kMushaf'], 'partial': P['kPartial'], 'reciter': P['kReciter'], 'tarawih': P['kTarawih']}
    written = []
    # ---------- صفحات القرّاء ----------
    for p in pages:
        x, items = p['x'], p['items']
        hrs = x.get('hours') or round(sum(i['d'] for i in items) / 3600, 1)
        name, desc0 = C.name(p), C.desc(p)
        rows = []
        for it in items:
            sub = [fmt_d(it['d'])]
            if it['who'] and it['who'] != p['who']: sub.append(E(C.who(it['who'])))
            ss = surahs_in(it['t'], it['u'])
            if ss: sub.append(' · '.join(surah_link(n, '../') for n in ss[:3]))
            rows.append(li(it, ' · '.join(sub)))
        rel = [q for q in same.get(norm(p['who']), []) if q is not p]
        chips = ''.join(f'<a href="{q["slug"]}.html">{E(C.name(q))}</a>' for q in rel)
        links = [f'<a href="{E(x["zip"])}" rel="nofollow">{E(C.t("zipAll", mb=x.get("mb", "")))}</a>' if x.get('zip') else '',
                 f'<a href="{E(x["m3u"])}" rel="nofollow">{E(P["m3u"])}</a>' if x.get('m3u') else '',
                 f'<a href="{E(x["page"])}" rel="nofollow">{E(P["arch"])}</a>' if x.get('page') else '']
        body = (f'<div class="chips">{"".join(l for l in links if l)}{chips}</div>'
                f'<h2>{E(C.t("recs", n=len(items)))}</h2><ul class="tr">{"".join(rows)}</ul>')
        title = C.t('recTitle', name=name)
        desc = C.t('recDesc', desc=desc0, n=len(items), h=hrs)
        lead = E(C.t('recLead', desc=desc0, n=len(items), h=hrs))
        ld = [{'@type': 'Person', 'name': C.who(p['who'])}] if p['kind'] != 'tarawih' and p['who'] != 'تلاوات متنوعة' else None
        written.append(page(C, f'reciter/{p["slug"]}.html', title, desc, name, [(P['navRec'], 'reciters.html'), (name, f'reciter/{p["slug"]}.html')],
                            body, lead, player=True, extra_ld=ld))
    # ---------- صفحات السور ----------
    ORDER = {'mushaf': 0, 'tarawih': 1, 'partial': 2, 'reciter': 3}
    for n in range(1, 115):
        ar, en, ay, pg = META[n - 1]
        sn = C.snames[n - 1]
        lst = sorted(by_surah[n], key=lambda pi: ORDER[pi[0]['kind']])
        groups = {}
        for p, it in lst: groups.setdefault(p['kind'], []).append((p, it))
        body = [f'<div class="chips"><a href="../quran/{n}.html">{E(P["qText"])}</a><a href="../mushaf.html#s={n}&amp;a=1">{E(P["readMushaf"])}</a>'
                + (f'<a href="{n - 1}.html">‹ {E(C.surah(n - 1))}</a>' if n > 1 else '')
                + (f'<a href="{n + 1}.html">{E(C.surah(n + 1))} ›</a>' if n < 114 else '') + '</div>']
        for k in ['mushaf', 'tarawih', 'partial', 'reciter']:
            g = groups.get(k)
            if not g: continue
            rows = []
            for p, it in g:
                who = C.name(p) if k == 'tarawih' else C.who(it['who'] if it['who'] and k == 'reciter' and p['who'] == 'تلاوات متنوعة' else p['who'])
                extra = f'{E(T(it["t"]))} · ' if k in ('partial', 'reciter') else ''
                if p.get('tag'): who += f' ({C.kindw(p["tag"])})'
                rows.append(li(it, f'{extra}{fmt_d(it["d"])} · <a href="../reciter/{p["slug"]}.html">{E(C.name(p))}</a>', t=who))
            body.append(f'<h2>{E(KIND[k])} ({len(g)})</h2><ul class="tr">{"".join(rows)}</ul>')
        cnt = len(lst)
        title = C.t('surTitle', s=sn)
        desc = C.t('surDesc', s=sn, en=en, n=cnt, ay=ay)
        lead = E(C.t('surLead', s=sn, no=n, ay=ay, pg=pg, n=cnt))
        written.append(page(C, f'surah/{n}.html', title, desc, C.surah(n), [(P['navSur'], 'surahs.html'), (C.surah(n), f'surah/{n}.html')],
                            ''.join(body), lead, player=True))
    # ---------- نص كل سورة مع ترجمة معانيها (أو تفسيرها المختصر في العربية) ----------
    key = None if C.ar else C.L['tr']
    if C.ar or key:
        meta = {} if C.ar else TRIDX[key]
        tdir, tlang = ('rtl', 'ar') if C.ar else (meta.get('direction', C.dir), meta.get('language_iso_code', C.code))
        src = (E(P['qSrc']) + ' (<a href="https://tafsir.net" rel="noopener">tafsir.net</a>)') if C.ar else \
            (E(C.t('qSrc', t=meta['title'], v=meta['version'])) + f' (<a href="https://quranenc.com/{C.L["qe"]}/browse/{key}" rel="noopener">QuranEnc.com</a>)')
        for n in range(1, 115):
            ar, en, ay, pg = META[n - 1]
            q = QTEXT[n - 1]
            tr = J(f'mushaf/t/{n}.json') if C.ar else TRF(key, n)
            assert len(q) == ay and len(tr) == ay, (C.code, n)
            rows = []
            for k, (qa, t) in enumerate(zip(q, tr), 1):
                if C.ar:
                    # المختصر: تفسير مجموعة آيات [من، إلى، النص] يُكتب مرة بعد آخرها، والكلمات المشروحة بين _ _ تُبرز كما في المصحف
                    a0, a1, t = (t[0], t[1], t[2]) if isinstance(t, list) else (k, k, t)
                    tx = '' if k != a1 else (f'<p class="tx"><b>{ind(a0) if a0 == a1 else ind(a0) + "–" + ind(a1)}.</b> '
                                             + re.sub(r'_([^_\n]+)_', r'<span class="qw">\1</span>', E(t)).replace('_', '') + '</p>')
                    rows.append(f'<div class="ay" id="a{k}"><p class="q">{E(qa)} {ind(k)}</p>{tx}</div>')
                    continue
                t, fn = (t[0], t[1]) if isinstance(t, list) else (t, '')
                # باقي اللغات: نص الآية يُملأ من mushaf/q/N.json (ملف واحد مشترك) حتى لا يتكرر في 43 نسخة
                rows.append(f'<div class="ay" id="a{k}"><p class="q"></p>'
                            f'<p class="tx">{"" if re.match(r"^\W{0,2}" + str(k) + r"\b", t) else f"<b>{k}.</b> "}{E(t)}</p>' + (f'<p class="fn">{E(fn)}</p>' if fn else '') + '</div>')
            bsm = f'<p class="q bsm">{E(QTEXT[0][0])}</p>' if n not in (1, 9) else ''
            fill = '' if C.ar else (f'<script>fetch("{"../" * 2}mushaf/q/{n}.json").then(function(r){{return r.json()}}).then(function(a){{var d="٠١٢٣٤٥٦٧٨٩";'
                                    'document.querySelectorAll(".ay .q").forEach(function(p,i){p.textContent=a[i]+" "+String(i+1).replace(/\\d/g,function(x){return d[x]})})}).catch(function(){})</script>')
            nav = (f'<div class="chips"><a href="../surah/{n}.html">{E(P["qListen"])}</a><a href="../mushaf.html#s={n}&amp;a=1">{E(P["readMushaf"])}</a>'
                   + (f'<a href="{n - 1}.html">‹ {E(C.surah(n - 1))}</a>' if n > 1 else '')
                   + (f'<a href="{n + 1}.html">{E(C.surah(n + 1))} ›</a>' if n < 114 else '') + '</div>')
            note = f'<p class="src">{E(P["qNote"])}</p>' if P.get('qNote') else ''
            body = nav + f'<div class="qs" lang="{tlang}" dir="{tdir}">' + bsm + ''.join(rows) + '</div>' + f'<p class="src">{src}</p>' + note + nav + fill
            sn = C.surah(n)
            written.append(page(C, f'quran/{n}.html', C.t('qTitle', s=sn), C.t('qDesc', s=sn, ay=ay), C.t('qH1', s=sn),
                                [(P['navSur'], 'surahs.html'), (sn, f'surah/{n}.html'), (P['qText'], f'quran/{n}.html')], body,
                                E(C.t('qLead', no=n, ay=ay, pg=pg)), quran=True))
    # ---------- الفهرسان ----------
    secs = []
    for k in ['mushaf', 'partial', 'reciter', 'tarawih']:
        ps = [p for p in pages if p['kind'] == k]
        a = ''.join(f'<a href="reciter/{p["slug"]}.html">{E(C.who(p["who"]) if p["who"] else (p["name"].replace("تراويح المسجد النبوي ", "") if C.ar else C.title(p["name"].replace("تراويح المسجد النبوي ", ""))))}'
                    f'<small>{E(C.t("nRec", n=len(p["items"])))}{(" · " + E(C.kindw(p["tag"]))) if p.get("tag") else ""}</small></a>' for p in ps)
        secs.append(f'<h2>{E(KIND[k])} ({len(ps)})</h2><div class="grid">{a}</div>')
    written.append(page(C, 'reciters.html', P['recsTitle'], P['recsDesc'], P['recsH1'], [(P['navRec'], 'reciters.html')], ''.join(secs), E(P['recsLead'])))
    cols = ''.join(f'<a href="surah/{n}.html">{n}. {E(C.surah(n))} <small>· {E(C.t("nTil", n=len(by_surah[n])))}</small></a>' for n in range(1, 115))
    written.append(page(C, 'surahs.html', P['sursTitle'], P['sursDesc'], P['sursH1'], [(P['navSur'], 'surahs.html')], f'<div class="cols">{cols}</div>', E(P['sursLead'])))
    return written


# ---------- نسخة الموقع والمصحف لكل لغة (من index.html و mushaf.html في الجذر) ----------
LOCAL_PAGES = {'mushaf.html', 'surahs.html', 'reciters.html', 'index.html', './'}


def set_block(s, name, content, anchor):
    """يكتب محتوى بين <!--name--> و<!--/name--> (ويضيفهما بعد anchor أول مرة)."""
    a, b = f'<!--{name}-->', f'<!--/{name}-->'
    if a in s: return s[:s.index(a) + len(a)] + content + s[s.index(b):]
    i = s.index(anchor) + len(anchor)
    return s[:i] + '\n' + a + content + b + s[i:]


def update_root(fname, path, anchor):
    """يحدّث قائمة اللغات وروابط hreflang في صفحة الجذر العربية."""
    p = os.path.join(ROOT, fname); s = open(p, encoding='utf-8').read()
    s = re.sub(r'/\*LANGS\*/.*?/\*/LANGS\*/', lambda m: '/*LANGS*/' + json.dumps(LANG_LIST, ensure_ascii=False, separators=(',', ':')) + '/*/LANGS*/', s, count=1, flags=re.S)
    s = set_block(s, 'HREFLANG', alternates(path), anchor)
    open(p, 'w', encoding='utf-8').write(s)
    return s


def bake(s, D):
    """يضع النص المترجم داخل العناصر الثابتة (ليقرأه قوقل دون تشغيل الجافاسكربت)."""
    def txt(m):
        k = m.group(2)
        return m.group(1) + E(D[k]) + m.group(4) if k in D and '<' not in D[k] else m.group(0)
    s = re.sub(r'(<[a-z0-9]+\b[^>]*\bdata-i18n="([\w]+)"[^>]*>)([^<]*)(<)', txt, s)
    s = re.sub(r'(<[a-z0-9]+\b[^>]*\bdata-i="([\w]+)"[^>]*>)([^<]*)(<)', txt, s)
    def aria(m):
        k = re.search(r'data-i(?:18n)?-aria="(\w+)"', m.group(0)).group(1)
        return re.sub(r'aria-label="[^"]*"', lambda _: f'aria-label="{E(D[k])}"', m.group(0)) if k in D else m.group(0)
    return re.sub(r'<[a-z0-9]+\b[^>]*\bdata-i(?:18n)?-aria="\w+"[^>]*>', aria, s)


def localize(s, C, fname, title, desc, og_title=None, og_desc=None, keywords=None):
    L, code = C.L, C.code
    path = '' if fname == 'index.html' else fname
    url = SITE + code + '/' + path
    ver = hashlib.md5(open(os.path.join(ROOT, 'i18n', code + '.js'), 'rb').read()).hexdigest()[:8]
    s = re.sub(r'<html lang="ar" dir="rtl"', f'<html lang="{code}" dir="{L["dir"]}"', s, count=1)
    s = re.sub(r'<title>.*?</title>', lambda m: f'<title>{E(title)}</title>', s, count=1, flags=re.S)
    s = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m.group(1) + E(desc), s, count=1)
    s = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + E(og_title or title), s, count=1)
    s = re.sub(r'(<meta property="og:description" content=")[^"]*', lambda m: m.group(1) + E(og_desc or desc), s, count=1)
    s = re.sub(r'(<meta property="og:url" content=")[^"]*', lambda m: m.group(1) + url, s, count=1)
    s = re.sub(r'(<link rel="canonical" href=")[^"]*', lambda m: m.group(1) + url, s, count=1)
    s = re.sub(r'(<meta property="og:locale" content=")[^"]*', lambda m: m.group(1) + L['loc'].replace('-', '_'), s, count=1)
    s = re.sub(r'(<meta name="apple-mobile-web-app-title" content=")[^"]*', lambda m: m.group(1) + E(L['p']['brand']), s, count=1)
    if keywords: s = re.sub(r'(<meta name="keywords" content=")[^"]*', lambda m: m.group(1) + E(keywords), s, count=1)
    s = re.sub(r'<meta name="google-site-verification"[^>]*>\n?', '', s)
    # الملفات المشتركة من الجذر، وصفحات اللغة تبقى داخل مجلدها
    def fix(m):
        v = m.group(2)
        if re.match(r'(?:[a-z]+:|//|/|#|\.\./|\{)', v) or v.split('?')[0].split('#')[0] in LOCAL_PAGES: return m.group(0)
        return f'{m.group(1)}="../{v}"'
    s = re.sub(r'\b(href|src)="([^"]+)"', fix, s)
    s = s.replace('url(mushaf/', 'url(../mushaf/')
    # نصوص اللغة قبل أي سكربت
    s = s.replace('<script>', f'<script src="../i18n/{code}.js?v={ver}"></script>\n<script>', 1)
    s = bake(s, L['t'] if fname == 'index.html' else L['m'])
    if fname == 'index.html':                    # JSON-LD مترجم
        P = L['p']
        def ld(m):
            g = json.loads(m.group(1))
            for o in g['@graph']:
                if o['@type'] == 'WebSite': o.update({'name': P['siteName'], 'url': url, 'inLanguage': code}); o['alternateName'] = ['Tartil', 'Tilawat min al-Quran al-Karim', 'ترتيل', 'تلاوات من القرآن الكريم']
                if o['@type'] == 'RadioStation': o.update({'name': title, 'url': url, 'description': desc, 'inLanguage': code})
            return '<script type="application/ld+json">\n' + json.dumps(g, ensure_ascii=False) + '\n</script>'
        s = re.sub(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', ld, s, count=1, flags=re.S)
    return s


def write_lang_js(C):
    L = C.L
    obj = {'code': C.code, 'dir': L['dir'], 'loc': L['loc'], 'name': L['name'], 'brand': L['p']['brand'], 'qe': L.get('qe', 'en'), 'tr': L.get('tr'), 'tf': L.get('tf'),
           't': L['t'], 'm': L['m'], 'x': L['x'], 's': L['s'], 'rec': L['rec']}
    os.makedirs(os.path.join(ROOT, 'i18n'), exist_ok=True)
    open(os.path.join(ROOT, 'i18n', C.code + '.js'), 'w', encoding='utf-8').write(
        '/* يولّده build_seo_pages.py من i18n/src/' + C.code + '.json — لا تعدّله يدويًا */\nwindow.TRL=' + json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + ';\n')


# ---------- التنفيذ ----------
os.makedirs(os.path.join(ROOT, 'mushaf', 'q'), exist_ok=True)
for _n, _q in enumerate(QTEXT, 1):
    json.dump(_q, open(os.path.join(ROOT, 'mushaf', 'q', f'{_n}.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
SHARED = shared_files()
ROOT_INDEX = update_root('index.html', '', '<link rel="canonical" href="https://trtel.vip/">')
ROOT_MUSHAF = update_root('mushaf.html', 'mushaf.html', '<link rel="canonical" href="https://trtel.vip/mushaf.html">')
REDIR = lang_redirect_js() if LANGS else ''
FIXED = [('', '1.0', 'weekly'), ('mushaf.html', '0.8', 'monthly'), ('reciters.html', '0.9', 'weekly'), ('surahs.html', '0.9', 'weekly')]
maps, total = [], 0
for code in ALL:
    C = Ctx(code)
    written = build_pages(C)
    fixed = list(FIXED)
    if C.ar: fixed += [('privacy.html', '0.2', 'yearly'), ('terms.html', '0.2', 'yearly')]
    else:
        write_lang_js(C); P = C.L['p']
        for fname, src, a in (('index.html', ROOT_INDEX, (P['homeTitle'], P['homeDesc'], P['homeOgTitle'], P['homeOgDesc'], P['homeKeywords'])),
                              ('mushaf.html', ROOT_MUSHAF, (P['musTitle'], P['musDesc']))):
            open(os.path.join(ROOT, code, fname), 'w', encoding='utf-8').write(localize(src, C, fname, *a))
    urls = fixed + [(w, '0.7', 'monthly') for w in written if w not in ('reciters.html', 'surahs.html')]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, pr, cf in urls:
        sm.append(f'  <url><loc>{SITE}{C.pre}{u}</loc><lastmod>{TODAY}</lastmod><changefreq>{cf}</changefreq><priority>{pr}</priority></url>')
    sm.append('</urlset>')
    name = f'sitemap-{code}.xml'
    open(os.path.join(ROOT, name), 'w', encoding='utf-8').write('\n'.join(sm) + '\n')
    maps.append(name); total += len(urls)
idx = ['<?xml version="1.0" encoding="UTF-8"?>', '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
idx += [f'  <sitemap><loc>{SITE}{m}</loc><lastmod>{TODAY}</lastmod></sitemap>' for m in maps]
idx.append('</sitemapindex>')
open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write('\n'.join(idx) + '\n')
print(len(ALL), 'languages;', total, 'urls in', len(maps), 'sitemaps;', sum(len(v) for v in by_surah.values()), 'surah entries')
