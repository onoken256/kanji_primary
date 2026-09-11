#!/usr/bin/env python3
"""各語の読みが、構成漢字の読み（連濁・促音・撥音便を許容）で説明できるか検査する。
説明できない語＝熟字訓 か 誤記 の候補として一覧表示する。"""
import sys, os, re, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('b', os.path.join(HERE, 'build.py'))
# build.py は main() を実行するので直接 import せず、関数だけ流用
src = open(os.path.join(HERE, 'build.py')).read().rsplit('\nmain()', 1)[0]
ns = {'__file__': os.path.join(HERE,'build.py')}
exec(compile(src, 'build.py', 'exec'), ns)
kanji = ns['load_kanji'](os.path.join(HERE, 'kanjidic2.xml.gz'))
sents, _ = ns['parse_sentences'](kanji)

DAKU = {'か':'が','き':'ぎ','く':'ぐ','け':'げ','こ':'ご','さ':'ざ','し':'じ','す':'ず','せ':'ぜ','そ':'ぞ',
        'た':'だ','ち':'ぢ','つ':'づ','て':'で','と':'ど','は':'ば','ひ':'び','ふ':'ぶ','へ':'べ','ほ':'ぼ'}
HANDAKU = {'は':'ぱ','ひ':'ぴ','ふ':'ぷ','へ':'ぺ','ほ':'ぽ'}

def variants(r):
    """1字分の読みの許容形を返す"""
    out = {r}
    if r and r[0] in DAKU: out.add(DAKU[r[0]] + r[1:])
    if r and r[0] in HANDAKU: out.add(HANDAKU[r[0]] + r[1:])
    if r and r[-1] in 'つちくき': out.add(r[:-1] + 'っ')   # 促音便 (学校 がっこう)
    if r.endswith('ん'): out.add(r)
    if r.endswith('う'): out.add(r[:-1] + 'っ')            # 法度など
    return out

def readings_of(c):
    info = kanji.get(c)
    if not info: return set()
    rs = set(info['on'])
    for k in info['kun']:
        stem = k.split('.')[0]
        rs.add(stem); rs.add(k.replace('.', ''))
    out = set()
    for r in rs:
        out |= variants(r)
    return out

def segmentable(word, reading, i=0, pos=0):
    if i == len(word): return pos == len(reading)
    for r in readings_of(word[i]):
        if r and reading.startswith(r, pos) and segmentable(word, reading, i+1, pos+len(r)):
            return True
    return False

seen = {}
for s in sents:
    for w in s['words']:
        seen.setdefault((w['k'], w['r']), s['line'])
bad = [(k, r, ln) for (k, r), ln in seen.items() if not segmentable(k, r)]
print(f"語（異なり） {len(seen)} / 要確認 {len(bad)}")
for k, r, ln in sorted(bad):
    print(f"  {k}《{r}》   ← {ln}")
