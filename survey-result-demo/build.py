"""data.json(관리자 API 스냅샷) -> public/index.html (데이터 내장, 키 불필요, 응답자 이름 제외)"""
import json, os
root = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(f'{root}/data.json', encoding='utf-8'))
share = {'now': d['now'], 'groups': d['groups'], 'overall': d['overall'], 'models': d['models'], 'cap': d.get('cap'),
         'stores': [{**{k: s[k] for k in ('code', 'name', 'group', 'total', 'done', 'cap', 'capDone')}, 'people': len(s['people'])} for s in d['stores']],
         'opinions': [{k: o.get(k) for k in ('store', 'group', 'style', 'mc', 'extra', 'text', 'at')} for o in d['opinions']]}
from classify import classify, grade_map
G = grade_map(share['stores']); share['grades'] = G
for o in share['opinions']: o['cat'] = classify(o['text'], o['mc'], cap=(o['style'] == share['cap'])); o['grade'] = G.get(o['store'], '')
for st in share['stores']: st['grade'] = G.get(st['name'], '')
sp = f'{root}/sales.json'
if os.path.exists(sp):
    sj = json.load(open(sp, encoding='utf-8')); share['sales_asof'] = sj['asof']
    for m in share['models']: m['sales'] = sj['styles'].get(m['code'])
tp = f'{root}/store_sales.json'
if os.path.exists(tp):
    tj = json.load(open(tp, encoding='utf-8')); share['top_asof'] = tj['asof']
    for m in share['models']: m['top'] = tj['top'].get(m['code'], [])
js = json.dumps(share, ensure_ascii=False).replace('</', '<\\/')
tpl = open(f'{root}/template.html', encoding='utf-8').read()
open(f'{root}/public/index.html', 'w', encoding='utf-8', newline='').write(tpl.replace('__DATA__', js))
print('written', os.path.getsize(f'{root}/public/index.html') // 1024, 'KB')
