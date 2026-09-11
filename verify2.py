#!/usr/bin/env python3
"""1字語の読みと、直後の送り仮名の整合を検査する。"""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE,'build.py')).read().rsplit('\nmain()',1)[0]
ns = {'__file__': os.path.join(HERE,'build.py')}
exec(compile(src,'build.py','exec'), ns)
kanji = ns['load_kanji'](os.path.join(HERE,'kanjidic2.xml.gz'))
TOKEN = re.compile(r'([一-鿿々]+)《([ぁ-んー]+)》')
flags = []
for g in range(1,7):
    for ln, line in enumerate(open(os.path.join(HERE,'data',f's{g}.txt')), 1):
        line = line.strip()
        for m in TOKEN.finditer(line):
            w, r = m.group(1), m.group(2)
            if len(w) != 1: continue
            info = kanji.get(w)
            if not info: continue
            tail = line[m.end():m.end()+4]
            tail = re.match(r'[ぁ-ん]*', tail).group(0)
            ok = r in info['on'] or r in info['kun']
            if not ok:
                for k in info['kun']:
                    if '.' in k:
                        stem, oku = k.split('.', 1)
                        if stem == r and tail.startswith(oku):
                            ok = True; break
            if not ok:
                flags.append(f"s{g}.txt:{ln} {w}《{r}》+「{tail}」 kun={info['kun'][:6]} on={info['on'][:3]} | {line}")
print('要確認', len(flags))
for f in flags: print(' ', f)
