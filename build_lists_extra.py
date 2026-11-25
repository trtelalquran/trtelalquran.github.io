#!/usr/bin/env python3
"""يبني قوائم M3U وروابط التحميل للمصاحف غير المكتملة وتلاوات القرّاء المتنوعة (2026-11-24).

المصدر: all-urls.txt (كل الروابط) وplaylist.json (القارئ والعنوان والمدة) وdownloads.json (الأسماء والأحجام).
الناتج: lists/<slug>.m3u و lists/<slug>-urls.txt، ومجموعتا partial و reciters في lists.json.
القرّاء الذين لهم مجلد في المكتبة يظهرون بأسمائهم، والباقي يُجمع في «تلاوات متنوعة».
"""
import json, re, os, urllib.parse, collections

SITE = 'https://trtel.vip/lists/'
# القرّاء الذين لهم مجلد مستقل في المكتبة (G:\ملفاتي\القرآن الكريم)
FOLDERS = {
    'د. سعود بن إبراهيم الشريم': 'saud-al-shuraim', 'خالد بن فهد الجليل': 'khalid-al-jaleel',
    'د. عبدالعزيز بن عبدالله الأحمد': 'abdulaziz-al-ahmad', 'ماجد الزامل': 'majed-al-zamil',
    'محمد المحيسني': 'muhammad-al-muhaisni', 'د. صلاح بن محمد البدير': 'salah-al-budair',
    'د. ماهر بن حمد المعيقلي': 'maher-al-muaiqly', 'د. عبدالله بن عبدالرحمن البعيجان': 'abdullah-al-buaijan',
    'عكاشة بن حسن كميني': 'okasha-kameny', 'حازم سيف': 'hazem-saif', 'د. الوليد بن خالد الشمسان': 'alwalid-al-shamsan',
    'أحمد بن طالب حميد': 'ahmad-bin-talib-humaid', 'د. علي بن عبدالله جابر': 'ali-jaber', 'يوسف العيدروس': 'yousef-al-aidarous',
    'أحمد بن محمد ديبان': 'ahmad-deban', 'د. محمد أيوب': 'muhammad-ayyub', 'د. بندر بن عبدالعزيز بليلة': 'bandar-baleela',
    'عبدالمحسن القاسم': 'abdulmohsen-al-qasim',  # 2026-11-25: تلاواته صارت في عنصره
}
MISC = 'تلاوات متنوعة'

P = json.load(open('playlist.json', encoding='utf-8'))
by = {x['u']: x for x in P['items']}
D = {x['id']: x for x in json.load(open('downloads.json', encoding='utf-8'))}
urls = [l.strip() for l in open('all-urls.txt', encoding='utf-8') if l.startswith('http')]
item = lambda u: re.search(r'/download/(trtel-alquran-[a-z0-9-]+)/', u).group(1)
fname = lambda u: urllib.parse.unquote(u.rsplit('/', 1)[1])[:-4]

os.makedirs('lists', exist_ok=True)

def write(slug, name, us):
    us = sorted(us, key=fname)
    m = ['#EXTM3U', '#PLAYLIST:' + name]
    secs = 0
    for u in us:
        x = by.get(u)
        secs += x['d'] if x else 0
        t = (x['t'] if x else re.sub(r'^\d{3}-\d{3} ', '', fname(u)))
        r = x['r'] if x else name
        m += ['#EXTINF:%d,%s - %s' % (x['d'] if x else -1, t, r), u]
    open('lists/%s.m3u' % slug, 'w', encoding='utf-8', newline='\n').write('\n'.join(m) + '\n')
    open('lists/%s-urls.txt' % slug, 'w', encoding='utf-8', newline='\n').write('\n'.join(us) + '\n')
    its = collections.Counter(item(u) for u in us)
    e = {'name': name, 'm3u': SITE + slug + '.m3u', 'urls': SITE + slug + '-urls.txt', 'n': len(us), 'hours': round(secs / 3600, 1)}
    if len(its) == 1:  # كل التلاوات في عنصر أرشيف واحد: له صفحة وملف ZIP
        i = next(iter(its)); e['page'] = 'https://archive.org/details/' + i; e['zip'] = 'https://archive.org/compress/' + i
        if i in D: e['mb'] = D[i]['mb']
    return e

L = json.load(open('lists.json', encoding='utf-8'))
for g in ('mushaf', 'tarawih'):
    for x in L[g]:
        i = x['page'].rsplit('/', 1)[1]
        if i in D: x['mb'] = D[i]['mb']

# المصاحف غير المكتملة
part = []
for i, d in D.items():
    if d['r'].startswith('مصحف غير مكتمل'):
        us = [u for u in urls if item(u) == i]
        part.append(write(i.replace('trtel-alquran-', ''), d['r'], us))
L['partial'] = part

# تلاوات القرّاء المتنوعة
old = [u for u in urls if not re.search(r'trtel-alquran-(mushaf|tarawih)-', u)]
grp = collections.defaultdict(list)
for u in old:
    r = by[u]['r'] if u in by else None
    grp[r if r in FOLDERS else MISC].append(u)
rec = [write('reciter-' + FOLDERS[r], r, grp[r]) for r in sorted(FOLDERS, key=lambda r: -len(grp[r])) if grp[r]]
rec.append(write('reciter-misc', MISC, grp[MISC]))
L['reciters'] = rec
L['all'] = {'n': len(urls), 'gb': round(sum(x['mb'] for x in D.values()) / 1000)}  # يظهر عند اختيار «تحميل كل التلاوات»
json.dump(L, open('lists.json', 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(len(part), 'partial;', len(rec), 'reciters;', sum(x['n'] for x in rec), 'files')
