#!/usr/bin/env python3
"""يبني بيانات المصحف من المصادر (تشغيل مرة واحدة):
  النص: risan/quran-json  data/quranpedia/qpc-hafs.json (مجمع الملك فهد، حفص)
  الصفحات/الأجزاء/أسماء السور وفهرس البحث: Tanzil (data/tanzil في المستودع نفسه)
  التفسير: «المختصر في التفسير» مركز تفسير (spa5k/tafsir_api ← QUL)
usage: build.py QURAN_JSON_DIR TAFSIR_DIR
"""
import json, os, sys
Q, TF = sys.argv[1], sys.argv[2]
out = os.path.dirname(os.path.abspath(__file__))
dump = lambda o, p: json.dump(o, open(os.path.join(out, p), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
q = json.load(open(f'{Q}/data/quranpedia/qpc-hafs.json', encoding='utf-8'))
clean = json.load(open(f'{Q}/data/tanzil/simple-clean.json', encoding='utf-8'))
ch = json.load(open(f'{Q}/data/tanzil/chapters.json', encoding='utf-8'))
idx = ch['indexes']
flat = [(int(s), a['verse'], a['text']) for s in sorted(q, key=int) for a in q[s]]
assert len(flat) == 6236
pos = {(s, a): i for i, (s, a, _) in enumerate(flat)}
starts = [pos[(p['sura'], p['aya'])] for p in idx['pages']] + [6236]
assert len(starts) == 605 and starts == sorted(starts)
os.makedirs(f'{out}/p', exist_ok=True); os.makedirs(f'{out}/t', exist_ok=True)
pageOf = {}
for n in range(604):
    rows = flat[starts[n]:starts[n + 1]]
    for s, a, _ in rows: pageOf[(s, a)] = n + 1
    dump([[s, a, t] for s, a, t in rows], f'p/{n + 1}.json')
BSM = 'بسم الله الرحمن الرحيم '
# أسماء السور كما في الموقع (index.html) لتطابق عناوين التلاوات
import re
_ix = open(os.path.join(out, '..', 'index.html'), encoding='utf-8').read()
AR = re.findall(r"'([^']+)'", re.search(r"const SURAH_AR = \[(.*?)\];", _ix).group(1)); assert len(AR) == 114
EN = re.findall(r"'([^']+)'", re.search(r"const SURAH_EN = \[(.*?)\];", _ix).group(1)); assert len(EN) == 114
for c in ch['chapters']: c['name'], c['transliteration'] = AR[c['id'] - 1], EN[c['id'] - 1]
meta = {
  'surahs': [[c['name'], c['transliteration'], c['total_verses'], pageOf[(c['id'], 1)]] for c in ch['chapters']],
  'pages': [[p['sura'], p['aya']] for p in idx['pages']],
  'bsm': q['1'][0]['text'],
  'juz': [[j['sura'], j['aya'], pageOf[(j['sura'], j['aya'])]] for j in idx['juzs']],
}
for c in ch['chapters']: assert len(q[str(c['id'])]) == c['total_verses'] == len(clean[str(c['id'])])
dump(meta, 'meta.json')
dump({'q': [[a['text'] for a in q[str(s)]] for s in range(1, 115)],
      'c': [[(a['text'][len(BSM):] if s > 1 and a['verse'] == 1 and a['text'].startswith(BSM) else a['text']) for a in clean[str(s)]] for s in range(1, 115)]}, 'search.json')
for s in range(1, 115):
    t = json.load(open(f'{TF}/{s}.json', encoding='utf-8'))
    t = t['ayahs'] if isinstance(t, dict) else t
    assert [x['ayah'] for x in t] == list(range(1, len(q[str(s)]) + 1)), s
    dump([x['text'].strip() for x in t], f't/{s}.json')
print('ok', len(flat))
