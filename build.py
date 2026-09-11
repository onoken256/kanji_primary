#!/usr/bin/env python3
"""短文プールを解析して、学年別カバレッジを確認し、アプリ用 data.js を生成する。"""
import gzip, json, re, sys, os, xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
KATA = {chr(c): chr(c-0x60) for c in range(0x30A1, 0x30F7)}
KANJI = re.compile(r'[一-鿿々]')
TOKEN = re.compile(r'([一-鿿々]+)《([ぁ-んー]+)》')

def load_kanji(path):
    root = ET.parse(gzip.open(path)).getroot()
    out = {}
    for ch in root.findall('character'):
        lit = ch.findtext('literal')
        g = ch.findtext('misc/grade')
        if g is None or int(g) > 6:
            continue
        on, kun = [], []
        for rm in ch.findall('reading_meaning/rmgroup/reading'):
            t = rm.text
            if rm.get('r_type') == 'ja_on':
                if '-' in t or '.' in t: continue
                on.append(''.join(KATA.get(c, c) for c in t))
            elif rm.get('r_type') == 'ja_kun':
                if t.startswith('-') or t.endswith('-'): continue
                kun.append(t)
        # 重複除去（順序保持）
        on = list(dict.fromkeys(on)); kun = list(dict.fromkeys(kun))
        out[lit] = {'g': int(g), 'on': on, 'kun': kun}
    return out

def parse_sentences(kanji):
    sents, errors = [], []
    for g in range(1, 7):
        p = os.path.join(HERE, 'data', f's{g}.txt')
        if not os.path.exists(p): continue
        for ln, line in enumerate(open(p), 1):
            line = line.strip()
            if not line or line.startswith('#'): continue
            # 未注釈の漢字が残っていないか
            stripped = TOKEN.sub('', line)
            if KANJI.search(stripped):
                errors.append(f's{g}.txt:{ln} 未注釈の漢字 {KANJI.findall(stripped)} → {line}')
                continue
            toks = TOKEN.findall(line)
            if not toks:
                errors.append(f's{g}.txt:{ln} 語が無い'); continue
            sents.append({'src': g, 'line': line,
                          'words': [{'k': w, 'r': r, 'g': max(kanji.get(c, {'g': 99})['g'] for c in w)}
                                    for w, r in toks]})
    return sents, errors

def main():
    kanji = load_kanji(os.path.join(HERE, 'kanjidic2.xml.gz'))
    sents, errors = parse_sentences(kanji)
    by_grade = {g: [] for g in range(1, 7)}
    for c, v in kanji.items():
        by_grade[v['g']].append(c)
    # カバレッジ：その学年の出題語として使える漢字
    covered = {g: set() for g in range(1, 7)}
    qcount = {g: 0 for g in range(1, 7)}
    for s in sents:
        for w in s['words']:
            if w['g'] <= 6:
                qcount[w['g']] += 1
                for c in w['k']:
                    if kanji[c]['g'] == w['g']:
                        covered[w['g']].add(c)
    print(f"短文 {len(sents)} 本 / エラー {len(errors)}")
    for e in errors[:40]: print('  !', e)
    for g in range(1, 7):
        miss = [c for c in by_grade[g] if c not in covered[g]]
        print(f"{g}年: {len(by_grade[g])}字中 {len(covered[g])}字カバー / 出題語 {qcount[g]} / 未カバー{len(miss)}: {''.join(miss)}")
    if '--emit' in sys.argv or '--build' in sys.argv:
        data = {'kanji': kanji,
                'sentences': [{'t': s['line'], 'lv': s['src']} for s in sents]}
        out = os.path.join(HERE, 'data.js')
        with open(out, 'w') as f:
            f.write('window.KANJI_DATA=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
        print('wrote', out, os.path.getsize(out), 'bytes')
        build_app()

def build_app():
    """src/app.html に data.js を埋め込んで、配布用の1ファイルHTMLを書き出す。"""
    src = open(os.path.join(HERE, 'src', 'app.html')).read()
    data = open(os.path.join(HERE, 'data.js')).read()
    if '__KANJI_DATA__' not in src:
        raise SystemExit('src/app.html に __KANJI_DATA__ のプレースホルダがありません')
    page = src.replace('__KANJI_DATA__', data)
    os.makedirs(os.path.join(HERE, 'dist'), exist_ok=True)
    # dist/app.html … Artifact 公開用（<html>/<body> はホスト側が付ける）
    with open(os.path.join(HERE, 'dist', 'app.html'), 'w') as f:
        f.write(page)
    # index.html … 単体で完結するHTML（GitHub Pages・ローカルで直接ひらく用）
    with open(os.path.join(HERE, 'index.html'), 'w') as f:
        f.write('<!doctype html>\n<html lang="ja">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
                '<meta name="description" content="小学校の学年別漢字配当表（1026字）から、'
                '漢字の読みを出題するドリル。選んだ学年より上の漢字には自動でふりがなが付きます。">\n'
                '<meta name="theme-color" content="#1F6B55">\n'
                '<style>html,body{margin:0}</style>\n</head>\n<body>\n'
                + page + '\n</body>\n</html>\n')
    print('wrote dist/app.html, index.html')

main()
