# -*- coding: utf-8 -*-
"""يفحص ملفات اللغات i18n/src/*.json مقابل en.json: المفاتيح الناقصة أو الزائدة، والمتغيرات {x} و$1 ووسوم HTML يجب أن تبقى كما هي."""
import json, glob, os, re, sys
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
en = json.load(open(os.path.join(D, 'en.json'), encoding='utf-8'))
OPT = {'alexaH', 'devIos', 'devAnd', 'loading', 'gb', 'mb', 'tfH', 'fatiha', 'nas'}
sig = lambda v: (sorted(re.findall(r'\{\w+\}|\$1', v)), sorted(re.findall(r'</?[a-z]+', v)))
bad = 0
for f in sorted(glob.glob(os.path.join(D, '*.json'))):
    code = os.path.basename(f)[:-5]
    if code in ('en',) or code.startswith('_'): continue
    L = json.load(open(f, encoding='utf-8'))
    for k in ('name', 'dir', 'loc', 'script'):
        if k not in L: print(code, 'missing top key', k); bad += 1
    for sec in 'tmxp':
        for k, v in en[sec].items():
            if k not in L.get(sec, {}):
                if k not in OPT: print(code, sec, 'MISSING', k); bad += 1
                continue
            if sig(v) != sig(L[sec][k]): print(code, sec, 'PLACEHOLDER/TAG MISMATCH', k, sig(v), sig(L[sec][k])); bad += 1
            if not L[sec][k].strip() and k != 'surah': print(code, sec, 'EMPTY', k); bad += 1
        for k in L.get(sec, {}):
            if k not in en[sec] and k not in OPT: print(code, sec, 'EXTRA', k); bad += 1
print('problems:', bad)
sys.exit(1 if bad else 0)
