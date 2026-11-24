#!/usr/bin/env python3
"""يستخرج «المختصر في تفسير القرآن الكريم» من قاعدة مركز تفسير الرسمية (quran.db من
huggingface.co/datasets/tafsircenter/tafsir-mcp-data، رخصة CC BY 4.0) إلى mushaf/t/{سورة}.json
وصفه: قائمة لكل سورة، العنصر i للآية i+1: نص، أو [من، إلى، نص] إن كان التفسير مشتركًا لمجموعة آيات.
usage: tafsir_official.py quran.db"""
import json, os, re, sqlite3, sys
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 't')
db = sqlite3.connect(sys.argv[1])
rows = db.execute('SELECT surahNo, ayahNo, Mukhtasarar FROM QuranTafseer ORDER BY surahNo, ayahNo').fetchall()
assert len(rows) == 6236, len(rows)
counts = [0] * 115
by = {}
for s, a, t in rows:
    s, a = int(s), int(a); counts[s] += 1; by[(s, a)] = (t or '').strip()
PRE = re.compile(r'^\s*(\d+)\s*(?:-\s*(\d+)\s*)+-\s*')
stats = {'groups': 0, 'empty': 0}
for s in range(1, 115):
    arr = []
    for a in range(1, counts[s] + 1):
        t = by[(s, a)]
        if not t: stats['empty'] += 1
        m = PRE.match(t)
        if m:
            nums = [int(x) for x in re.findall(r'\d+', m.group(0))]
            if a in nums or nums[0] <= a <= nums[-1]:
                arr.append([nums[0], nums[-1], t[m.end():].strip()]); stats['groups'] += 1; continue
        arr.append(t)
    json.dump(arr, open(f'{out}/{s}.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('ok', stats)
