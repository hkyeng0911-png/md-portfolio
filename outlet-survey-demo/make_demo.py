"""아울렛 전용 상품 수요조사 결과 페이지 — 포트폴리오 시연판.
실제 결과 페이지와 같은 구조로 가상 매장 10곳·가상 응답·자동 요약을 만들어
template.html 에 심는다(public/index.html, public/outlet_survey_result.csv).
실행: python make_demo.py
"""
import csv, json, os, random
from collections import Counter

random.seed(1030)
HERE = os.path.dirname(os.path.abspath(__file__))

SECTIONS = [
    {'id': 'B', 'title': '온라인 전용 데님 판매 경험', 'note': '기준 상품: 온라인 전용 슬림 스트레이트 · 테이퍼드 슬림 (59,000원, 71~91)', 'products': True},
    {'id': 'C', 'title': '아울렛 전용 데님 — 필요한 핏'},
    {'id': 'D', 'title': '기본 이너류(티셔츠) 수요', 'note': '아울렛 전용으로 필요한 기본 이너 기준으로 답해 주세요'},
    {'id': 'E', 'title': '종합'},
]
Q = [
    {'id': 'B1', 'sec': 'B', 'type': 'single', 'req': True, 'q': '온라인 전용 데님을 가장 많이 구매한 연령대는?', 'opts': ['20대', '30대', '40대', '50대 이상']},
    {'id': 'B2', 'sec': 'B', 'type': 'multi', 'req': True, 'max': 2, 'exclusive': '부족한 점 없음', 'q': '판매하면서 부족했던 점은? (최대 2개)', 'opts': ['핏 종류', '사이즈 구성', '컬러', '기장', '소재·두께', '신축성', '부족한 점 없음']},
    {'id': 'C1', 'sec': 'C', 'type': 'single', 'req': True, 'q': '아울렛 전용 남성 데님에 가장 필요한 핏은?', 'opts': ['슬림 스트레이트', '테이퍼드 슬림', '스트레이트', '와이드']},
    {'id': 'C2', 'sec': 'C', 'type': 'multi', 'req': True, 'max': 2, 'q': '필요한 컬러는? (최대 2개)', 'opts': ['블랙', '다크 인디고', '미디엄 인디고', '라이트(연청)', '그레이']},
    {'id': 'C3', 'sec': 'C', 'type': 'single', 'req': True, 'q': '허리 형태는?', 'opts': ['반밴딩', '밴딩', '일반(지퍼·버튼)', '상관없음']},
    {'id': 'C4', 'sec': 'C', 'type': 'multi', 'req': True, 'max': 2, 'exclusive': '없음', 'q': '부족하거나 더 필요한 사이즈는? (최대 2개)', 'opts': ['71 이하', '76~81', '86~91', '96 이상', '없음']},
    {'id': 'C5', 'sec': 'C', 'type': 'single', 'req': True, 'q': '적정 판매가는?', 'opts': ['49,000원', '59,000원 (현재)', '69,000원 이상']},
    {'id': 'C6', 'sec': 'C', 'type': 'single', 'req': True, 'q': '여성 데님도 필요한가요?', 'opts': ['필요', '불필요']},
    {'id': 'C7', 'sec': 'C', 'type': 'single', 'req': True, 'dep': ['C6', '필요'], 'q': '여성 데님에 필요한 핏은?', 'opts': ['슬림', '스트레이트', '와이드', '부츠컷']},
    {'id': 'C8', 'sec': 'C', 'type': 'text', 'req': False, 'q': '데님 관련 의견 (기장·신축성 등, 선택)'},
    {'id': 'D1', 'sec': 'D', 'type': 'single', 'req': True, 'q': '필요한 기본 이너의 소매 길이는?', 'opts': ['반팔', '긴팔']},
    {'id': 'D2', 'sec': 'D', 'type': 'single', 'req': True, 'q': '필요한 넥 형태는?', 'opts': ['라운드넥', '헨리넥', '브이넥', '터틀넥', '카라']},
    {'id': 'D3', 'sec': 'D', 'type': 'single', 'req': True, 'q': '기모 여부는?', 'opts': ['기모', '무기모']},
    {'id': 'D4', 'sec': 'D', 'type': 'single', 'req': True, 'q': '필요한 핏은?', 'opts': ['슬림', '레귤러', '오버핏']},
    {'id': 'D5', 'sec': 'D', 'type': 'single', 'req': True, 'q': '적정 판매가는?', 'opts': ['29,000원', '39,000원', '49,000원 이상']},
    {'id': 'D6', 'sec': 'D', 'type': 'text', 'req': False, 'q': '이너 관련 의견 (고객이 찾는데 없는 품목 등, 선택)'},
    {'id': 'E1', 'sec': 'E', 'type': 'multi', 'req': True, 'max': 2, 'q': '아울렛 전용으로 필요한 상품 카테고리는? (최대 2개)', 'opts': ['남성 데님', '여성 데님', '기본 이너(티셔츠)', '니트·가디건', '점퍼·아우터', '셔츠', '면팬츠·슬랙스', '맨투맨·후드']},
]
# 선택지별 가중치 (아울렛 고객층이 40~50대라는 가정의 가상 분포)
W = {'B1': [1, 2, 6, 4], 'B2': [5, 3, 6, 2, 2, 3, 1], 'C1': [6, 2, 3, 1], 'C2': [3, 7, 6, 1, 1], 'C3': [4, 2, 5, 1], 'C4': [1, 3, 4, 3, 2],
     'C5': [3, 6, 1], 'C6': [6, 4], 'C7': [3, 4, 2, 1], 'D1': [4, 6], 'D2': [7, 3, 2, 2, 1], 'D3': [4, 6], 'D4': [2, 7, 1], 'D5': [5, 5, 1],
     'E1': [7, 3, 6, 3, 3, 2, 3, 2]}
DENIM_TXT = ['유행 핏보다 편하게 입는 일자핏을 많이 찾으십니다', '신축성 있는 원단이면 좋겠다는 의견이 많습니다', '기장 수선 문의가 많아 기장 선택지가 있으면 좋겠습니다',
             '워싱 없는 깔끔한 진청을 찾는 고객이 많습니다', '허리가 편한 반밴딩을 선호하십니다', '블랙진 문의가 꾸준합니다']
INNER_TXT = ['무지 라운드 긴팔을 가장 많이 찾으십니다', '겨울에는 기모 이너 문의가 많습니다', '목이 늘어나지 않는 두께감이 중요하다고 하십니다', '헨리넥 문의도 종종 있습니다']

stores = [{'code': f'S{i + 1:02d}', 'name': f'아울렛 {chr(65 + i)}점', 'group': '신상입고매장' if i < 5 else '신상미입고매장'} for i in range(10)]

def pick(q):
    w = W[q['id']]
    if q['type'] == 'single':
        return random.choices(q['opts'], weights=w)[0]
    k = random.choice([1, 2, 2])
    out = []
    while len(out) < k:
        o = random.choices(q['opts'], weights=w)[0]
        if o not in out: out.append(o)
    ex = q.get('exclusive')
    if ex and ex in out: out = [ex]
    return out

responses = []
for i, s in enumerate(stores):
    a = {}
    for q in Q:
        if q.get('dep') and a.get(q['dep'][0]) != q['dep'][1]: continue
        if q['type'] == 'text':
            pool = DENIM_TXT if q['id'] == 'C8' else INNER_TXT
            if random.random() < 0.7: a[q['id']] = random.choice(pool)
            continue
        a[q['id']] = pick(q)
    responses.append({'store_code': s['code'], 'store_name': s['name'], 'grp': s['group'], 'answers': a, 'complete': True,
                      'updated_at': f'2026-10-2{random.randint(6, 8)} {random.randint(10, 18)}:{random.randint(10, 59)}:00'})

# 자동 요약 (가상 응답 집계로 생성)
def cnt(qid):
    c = Counter()
    for r in responses:
        v = r['answers'].get(qid)
        for x in (v if isinstance(v, list) else [v] if v else []): c[x] += 1
    return c.most_common()
def top(qid, k=2): return '·'.join(f'{o}({n}곳)' for o, n in cnt(qid)[:k])
ntext = sum(1 for r in responses for k in ('C8', 'D6') if r['answers'].get(k))
summary = '\n'.join([
    f'조사 개요: 아울렛 10개점(신상 입고 5곳·미입고 5곳) 매니저에게 아울렛 전용 데님과 기본 이너에 필요한 사양을 물었습니다. 10개점 모두 응답했고 자유의견은 {ntext}건입니다. (포트폴리오용 가상 데이터)',
    f'# 1. 데님: {cnt("C1")[0][0]} 선호가 가장 많음',
    f'- 필요한 핏은 {top("C1", 3)} 순입니다.',
    f'- 컬러는 {top("C2", 3)}, 허리는 {top("C3")} 응답이 많습니다.',
    f'- 기존 온라인 전용 데님에서 부족했던 점은 {top("B2")}입니다. 적정 판매가는 {cnt("C5")[0][0]}가 가장 많습니다.',
    f'# 2. 기본 이너: {cnt("D1")[0][0]} · {cnt("D2")[0][0]} 수요',
    f'- 핏은 {top("D4")}, 기모는 {top("D3")}, 적정 판매가는 {top("D5")}입니다.',
    f'# 3. 종합: 아울렛 전용으로 필요한 카테고리는 {top("E1", 3)}',
])
data = {'now': '2026-10-28 11:00:00', 'sections': SECTIONS, 'questions': Q, 'stores': stores, 'responses': responses,
        'summary': summary, 'summary_at': '2026-10-28 11:00'}
tpl = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
open(os.path.join(HERE, 'public', 'index.html'), 'w', encoding='utf-8').write(tpl.replace('/*DATA*/', json.dumps(data, ensure_ascii=False).replace('</', '<\\/')))
with open(os.path.join(HERE, 'public', 'outlet_survey_result.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['매장코드', '매장', '구분', '응답시각'] + [f"{q['id']}. {q['q']}" for q in Q])
    for r in responses:
        a = r['answers']
        w.writerow([r['store_code'], r['store_name'], r['grp'], r['updated_at']] +
                   [', '.join(a[q['id']]) if isinstance(a.get(q['id']), list) else a.get(q['id'], '') for q in Q])
print('stores', len(stores), 'responses', len(responses), 'texts', ntext)
