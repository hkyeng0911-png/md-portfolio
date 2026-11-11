"""포트폴리오 시연용 가상 데이터 생성.
실제 결과 페이지와 같은 구조(data.json / sales.json / store_sales.json / grades.json)로
가상 매장·가상 품번·가상 의견을 만든다. 실제 매장명·품번·판매·의견은 들어가지 않는다.
실행: python make_demo_data.py  →  python build.py
"""
import json, os, random

random.seed(275)
root = os.path.dirname(os.path.abspath(__file__))
NOW = '2026-11-05 08:00:00'
GROUPS = ['서브라인 매장', '백화점', '아울렛', '할인점', '대리점']

# ---------- 매장 (가상)
stores = []
plan = [('서브라인 매장', 7, '서브'), ('백화점', 12, '백화점'), ('아울렛', 11, '아울렛'), ('할인점', 6, '할인점'), ('대리점', 4, '대리점')]
for g, n, label in plan:
    for i in range(1, n + 1):
        stores.append({'code': f'S{len(stores) + 1:03d}', 'name': f'{label} {chr(64 + i)}점', 'group': g})

# ---------- 품번 (가상) — 코드 5~6번째 글자가 복종
ITEMS = [('AP', '볼캡', 39000), ('AT', '레더 벨트', 59000), ('DJ', '트러커 데님 자켓', 189000), ('DP', '와이드 데님 팬츠', 129000),
         ('DP', '부츠컷 데님 팬츠', 139000), ('DW', '후드 다운 점퍼', 329000), ('JP', '코튼 워크 자켓', 199000), ('LI', '레더 라이더 자켓', 269000),
         ('KC', '케이블 니트 가디건', 119000), ('KT', '크루넥 니트', 99000), ('SH', '체크 셔츠', 89000), ('TJ', '스웨트 후드 집업', 129000),
         ('TS', '그래픽 맨투맨', 79000), ('TS', '로고 후디', 89000), ('TP', '스웨트 조거 팬츠', 79000), ('PT', '카고 팬츠', 109000)]
COLORS = [('19', 'BLACK'), ('11', 'LIGHT GREY'), ('06', 'NAVY'), ('83', 'BEIGE'), ('15', 'CHARCOAL'), ('93', 'INDIGO')]
models = []
for i in range(40):
    cat, base, price = ITEMS[i % len(ITEMS)]
    sub = i % 4 == 3
    gender = random.choice(['남성', '여성', '유니'])
    name = ('[서브] ' if sub else '') + f'{gender} {base}'
    code = f'DEMO{cat}{i + 1:03d}P'
    cols = random.sample(COLORS, random.choice([1, 2, 2, 3]))
    models.append({'code': code, 'name': name, 'colors': ', '.join(c[1] for c in cols), 'sale': price, 'img': f'img/{code}.svg',
                   'cap': False, '_cols': cols, '_cat': cat})
cap = {'code': 'DEMOAP900P', 'name': '[콜라보] 5패널 로고 캡모자', 'colors': 'BEIGE, NAVY', 'sale': 49000, 'img': 'img/DEMOAP900P.svg',
       'cap': True, '_cols': [('83', 'BEIGE'), ('06', 'NAVY')], '_cat': 'AP'}
models.insert(0, cap)

# ---------- 의견 문장 (일반적인 표현으로 새로 작성)
TEXTS = {
    'design': ['핏이 예쁘다는 반응이 많습니다', '컬러가 더 다양했으면 좋겠다고 하십니다', '입어보시면 생각보다 예쁘다고 하세요', '디자인이 심플해서 무난하게 찾으십니다',
               '기장이 조금 짧다는 의견이 있습니다', '로고 포인트를 좋아하십니다', '소재가 부드럽다고 만족하십니다', '사이즈가 크게 나온다는 의견이 있어요',
               '어깨 라인이 예쁘다는 반응입니다', '워싱 색감이 좋다고 하십니다', '두께감이 적당해서 지금 입기 좋다고 하세요', '디테일이 많아 호불호가 있습니다'],
    'quality': ['봉제 마감이 아쉽다는 의견이 있습니다', '원단이 얇다는 말씀을 하십니다', '보풀이 걱정된다는 문의가 있었습니다', '퀄리티가 좋다는 반응입니다'],
    'price': ['가격이 조금 부담스럽다고 하십니다', '할인 행사 때 다시 오신다고 하세요', '가격 대비 만족도가 높습니다', '비슷한 상품보다 비싸다는 의견입니다'],
    'soso': ['보통 반응입니다', '관심은 있지만 구매로 이어지진 않습니다', '시착은 하시는데 고민하십니다'],
    'none': ['아직 반응이 없습니다', '문의가 거의 없습니다', '입고 전이라 반응을 모르겠습니다', ''],
}
OTHER_EXTRA = ['날씨가 추워지면 더 나갈 것 같습니다', '사이즈가 없어 추가 입고 문의가 있습니다', '진열 위치를 바꾸니 반응이 생겼습니다']
MC = ['design', 'design', 'design', 'quality', 'price', 'soso', 'none', 'none']
CAP_TEXT = ['모자 깊이가 얕다고 하십니다', '로고가 예쁘다는 반응입니다', '챙이 짧다는 의견이 있습니다', '색상이 더 있었으면 좋겠다고 하세요', '아직 찾는 분이 없습니다', '']

# ---------- 매장별 응답
opinions, people = [], {}
for st in stores:
    carried = random.sample(models[1:], random.randint(12, 22))
    st['total'] = len(carried)
    st['done'] = st['total'] if random.random() < 0.8 else random.randint(0, st['total'] - 1)
    st['cap'] = random.random() < 0.5
    st['capDone'] = st['cap'] and random.random() < 0.85
    st['people'] = ['응답자'] * random.choice([1, 1, 1, 2])
    st['last'] = '2026-11-0' + str(random.randint(1, 4)) + ' 1' + str(random.randint(0, 8)) + ':00:00'
    for m in carried[:st['done']]:
        mc = random.choice(MC)
        text = random.choice(TEXTS[mc]) if random.random() < 0.85 else random.choice(OTHER_EXTRA)
        opinions.append({'store': st['name'], 'group': st['group'], 'who': '응답자', 'style': m['code'], 'mc': mc, 'extra': [],
                         'text': text, 'at': f'2026-11-0{random.randint(1, 4)} {random.randint(10, 19)}:{random.randint(10, 59)}:00', 'complete': True})
    if st['capDone']:
        ex = random.sample(['price', 'size', 'logo', 'color', 'material'], random.choice([0, 1, 1, 2]))
        opinions.append({'store': st['name'], 'group': st['group'], 'who': '응답자', 'style': cap['code'],
                         'mc': random.choice(['great', 'good', 'soso', 'weak', 'none', 'none', 'soso']), 'extra': ex or ['none'],
                         'text': random.choice(CAP_TEXT), 'at': '2026-11-03 14:00:00', 'complete': True})

# ---------- 품번별 집계
KEYS = ['design', 'quality', 'price', 'soso', 'none']
CAPK = ['great', 'good', 'soso', 'weak', 'none']
for m in models:
    ops = [o for o in opinions if o['style'] == m['code']]
    m['stores'] = sum(1 for st in stores if st['cap']) if m['cap'] else max(len(ops), random.randint(10, 30))
    m['n'] = len(ops)
    keys = CAPK if m['cap'] else KEYS
    m['dist'] = {k: sum(1 for o in ops if o['mc'] == k) for k in keys}
    if m['cap']:
        q = {k: 0 for k in ['price', 'size', 'logo', 'color', 'material', 'none']}
        for o in ops:
            for e in o['extra']: q[e] += 1
        m['q2'] = q; m['q2n'] = len(ops)

overall = {'responses': len(opinions), 'people': sum(len(s['people']) for s in stores), 'stores': len(stores),
           'capStores': sum(1 for s in stores if s['cap']), 'capDone': sum(1 for s in stores if s['capDone'])}
data = {'now': NOW, 'groups': GROUPS, 'cap': cap['code'], 'overall': overall,
        'models': [{k: v for k, v in m.items() if not k.startswith('_')} for m in models], 'stores': stores, 'opinions': opinions}
json.dump(data, open(f'{root}/data.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ---------- 판매 (가상)
styles = {}
for m in models:
    cols = []
    for c, nm in m['_cols']:
        inq = random.choice([150, 200, 300, 400, 500])
        sold = int(inq * random.uniform(0.05, 0.75))
        cost = round(m['sale'] * random.uniform(0.22, 0.3), -2)
        cols.append({'code': c, 'name': nm, 'plan': inq, 'in': inq, 'sold': sold, 'first_ship': '2026-09-15', 'cost': cost, 'unit_cost': cost,
                     'unit_sale': m['sale'], 'store_stock': int((inq - sold) * 0.6), 'hq_stock': int((inq - sold) * 0.4), 'rate': round(sold / inq * 100, 1)})
    tin = sum(c['in'] for c in cols); tsold = sum(c['sold'] for c in cols)
    styles[m['code']] = {'name': m['name'], 'tag': m['sale'], 'price': m['sale'], 'normal': m['sale'], 'cost': cols[0]['cost'],
                         'first_in': '2026-09-12', 'first_ship': '2026-09-15', 'price_changed': None, 'colors': cols,
                         'in': tin, 'sold': tsold, 'rate': round(tsold / tin * 100, 1), 'unit_cost': cols[0]['cost'], 'unit_sale': m['sale']}
json.dump({'asof': '2026-11-03 (가상)', 'styles': styles}, open(f'{root}/sales.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
top = {m['code']: [{'store': s['name'], 'qty': q, 'rank': r + 1} for r, (s, q) in
                   enumerate(zip(random.sample(stores, 3), sorted(random.sample(range(2, 18), 3), reverse=True)))] for m in models}
json.dump({'asof': '2026-11-03 (가상)', 'top': top}, open(f'{root}/store_sales.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump({s['name']: random.choice('AABBC') for s in stores if s['group'] != '서브라인 매장'},
          open(f'{root}/grades.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ---------- 상품 이미지 대신 쓸 단순 아이콘
os.makedirs(f'{root}/public/img', exist_ok=True)
for m in models:
    hue = sum(map(ord, m['code'])) % 360
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80"><rect width="80" height="80" rx="8" fill="hsl({hue},30%,88%)"/>'
           f'<text x="40" y="46" font-size="16" text-anchor="middle" font-family="sans-serif" fill="hsl({hue},35%,35%)">{m["_cat"]}</text></svg>')
    open(f'{root}/public/img/{m["code"]}.svg', 'w', encoding='utf-8').write(svg)
print('stores', len(stores), 'models', len(models), 'opinions', len(opinions))
