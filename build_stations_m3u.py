#!/usr/bin/env python3
"""يبني قائمتي M3U لإذاعتي الموقع المتزامنتين من stations.json بنفس ترتيب index.html (2026-11-27).

lists/radio-mushaf.m3u  : «إذاعة لكل الأئمة»: الختمة k، السورة n يقرؤها المصحف (n+k) mod N.
lists/radio-tarawih.m3u : «إذاعة التراويح»: ختمات تخلط السنوات (قديمة ثم جديدة)، نفس خوارزمية mkSrc في index.html.
يُعاد تشغيله عند تغيير stations.json أو خوارزمية المحطتين. الروابط من all-urls.txt.
"""
import json, re, urllib.parse
from math import gcd

S = json.load(open('stations.json', encoding='utf-8'))
URL = {}
for l in open('all-urls.txt', encoding='utf-8'):
    l = l.strip()
    m = re.search(r'/download/trtel-alquran-([a-z0-9-]+)/(\d{3})%20', l)
    if m and not re.search(r'%20\d+-\d+\.mp3$', l): URL.setdefault((m.group(1), int(m.group(2))), l)
name = lambda u: urllib.parse.unquote(u.rsplit('/', 1)[1])[4:-4]

def one(m):
    sk = m.get('skip', []); a = {}; j = 0
    for n in range(1, 115):
        if n in sk: continue
        a[n] = (m, m['d'][j], URL[(m['id'], n)]); j += 1
    return a

def write(path, title, items, label):
    L = ['#EXTM3U', '#PLAYLIST:' + title]
    for m, d, u in items: L += [f'#EXTINF:{d},سورة {name(u)} - {label(m)}', u]
    open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')
    print(path, len(items), 'items', round(sum(x[1] for x in items) / 86400, 1), 'days')

M = [one(m) for m in S['mushaf']]; N = len(M)
items = [M[(n - 1 + k) % N][n] for k in range(N) for n in range(1, 115) if n in M[(n - 1 + k) % N]]
write('lists/radio-mushaf.m3u', 'إذاعة المصاحف: كل سورة بقراءة إمام مختلف', items, lambda m: m['r'])

ys = sorted(S['tarawih'], key=lambda y: y['y']); h = -(-len(ys) // 2); o, w = ys[:h], ys[h:]
def mix(Ls, m):
    while gcd(m, len(Ls)) > 1: m += 1
    return [Ls[i * m % len(Ls)] for i in range(len(Ls))]
O, W = mix(o, 7), mix(w, 5); A = []
for i in range(h):
    A.append(O[i])
    if i < len(W): A.append(W[i])
allY = [one(y) for y in A]; N = len(A); stp = 12
while gcd(stp, N) > 1: stp += 1
items = []
for k in range(N):
    for n in range(1, 115):
        j = (n - 1 + stp * k) % N
        it = allY[j].get(n) or allY[(j + 17) % N].get(n)
        if it: items.append(it)
write('lists/radio-tarawih.m3u', 'إذاعة التراويح: كل سورة من سنة مختلفة', items, lambda m: f"تراويح المسجد النبوي {m['y']}هـ")
