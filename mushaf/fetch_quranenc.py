# -*- coding: utf-8 -*-
"""يجلب ترجمات معاني القرآن من QuranEnc.com (موسوعة القرآن الكريم) كما هي بلا أي تعديل، ويحفظ نسخة ثابتة في mushaf/tr/.

التشغيل (من GitHub Actions لأن الموقع محجوب عن بعض الشبكات):
  python mushaf/fetch_quranenc.py list   → mushaf/tr/catalog.json (كل الترجمات المتاحة وإصداراتها)
  python mushaf/fetch_quranenc.py sync   → يجلب ما في mushaf/tr/select.json إن تغيّر إصداره، ويكتب mushaf/tr/index.json

الملفات: mushaf/tr/<key>/<1..114>.json = قائمة بعدد الآيات؛ كل عنصر نص الترجمة، أو [النص، الحواشي] إن وُجدت حواشٍ.
شروط QuranEnc: لا تعديل، ذكر المصدر ورقم الإصدار، والتحديث لآخر إصدار. لذلك لا يُحرَّر أي ملف هنا يدويًا.
"""
import json, os, sys, time, urllib.request

API = 'https://quranenc.com/api/v1/'
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tr')
AYAT = [s[2] for s in json.load(open(os.path.join(HERE, '..', 'meta.json'), encoding='utf-8'))['surahs']]


def get(path, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(API + path, headers={'User-Agent': 'Mozilla/5.0 (static-site sync)', 'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(3 * (i + 1))


def dump(path, obj, **kw):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'), **kw)


def catalog():
    out = []
    for t in get('translations/list/?localization=en')['translations']:
        out.append({k: t.get(k) for k in ('key', 'language_iso_code', 'direction', 'version', 'last_update', 'title', 'description')})
    try:
        nat = {t['key']: t.get('title') for t in get('translations/list/')['translations']}
    except Exception:
        nat = {}
    for t in out: t['title_ar'] = None
    try:
        ar = {t['key']: (t.get('title'), t.get('description')) for t in get('translations/list/?localization=ar')['translations']}
        for t in out: t['title_ar'], t['description_ar'] = ar.get(t['key'], (None, None))
    except Exception as e:
        print('ar titles failed', e)
    return out


def fetch(key):
    """يرجع 114 قائمة بعد التحقق من اكتمال عدد الآيات؛ وإلا يرفع خطأ فلا يُكتب شيء ناقص."""
    res = []
    for s in range(1, 115):
        rows = get(f'translation/sura/{key}/{s}')['result']
        by = {int(r['aya']): r for r in rows}
        if sorted(by) != list(range(1, AYAT[s - 1] + 1)):
            raise ValueError(f'{key} sura {s}: got {len(by)} ayat, expected {AYAT[s - 1]}')
        one = []
        for a in range(1, AYAT[s - 1] + 1):
            r = by[a]; tx, fn = r.get('translation') or '', r.get('footnotes') or ''
            one.append([tx, fn] if fn else tx)
        res.append(one)
        time.sleep(0.15)
    return res


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'sync'
    cat = catalog()
    dump(os.path.join(HERE, 'catalog.json'), cat, indent=None)
    print(len(cat), 'translations in catalog;', len({t['language_iso_code'] for t in cat}), 'languages')
    try:   # أسماء السور الرسمية بكل لغة متاحة
        names = {}
        for loc in get('translations/sowar_locales'):
            try:
                d = get('translations/sowar_names?iso_code=' + loc)
                names[loc] = [d[str(i)] for i in range(1, 115)]
            except Exception as e:
                print('sowar', loc, e)
        if names: dump(os.path.join(HERE, 'sowar.json'), names)
        print(len(names), 'sowar locales')
    except Exception as e:
        print('sowar names failed', e)
    if mode == 'list': return
    sel = json.load(open(os.path.join(HERE, 'select.json'), encoding='utf-8'))      # {lang: {"tr": key, "tf": key}}
    idx_path = os.path.join(HERE, 'index.json')
    old = json.load(open(idx_path, encoding='utf-8')) if os.path.exists(idx_path) else {}
    by_key = {t['key']: t for t in cat}
    new, changed, failed = {}, [], []
    for key in sorted({k for v in sel.values() for k in v.values() if k}):
        t = by_key.get(key)
        if not t:
            print('MISSING in catalog:', key); failed.append(key)
            if key in old: new[key] = old[key]
            continue
        have = old.get(key)
        if have and have.get('version') == t['version'] and have.get('last_update') == t['last_update'] and os.path.exists(os.path.join(HERE, key, '114.json')):
            new[key] = have; continue
        try:
            data = fetch(key)
        except Exception as e:
            print('FAILED', key, e); failed.append(key)
            if have: new[key] = have
            continue
        for s, one in enumerate(data, 1): dump(os.path.join(HERE, key, f'{s}.json'), one)
        new[key] = {k: t.get(k) for k in ('language_iso_code', 'direction', 'version', 'last_update', 'title', 'title_ar')}
        changed.append(key); print('updated', key, t['version'])
    dump(idx_path, new, indent=None)
    print('changed:', len(changed), 'failed:', len(failed))
    open(os.path.join(HERE, 'last_sync.txt'), 'w').write('changed: ' + ', '.join(changed) + '\nfailed: ' + ', '.join(failed) + '\n')


if __name__ == '__main__':
    main()
