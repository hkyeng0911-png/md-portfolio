#@title 📈 네이버 데이터랩 연계 복종별 판매추이 예측
#@markdown **① 네이버 API 키** — developers.naver.com → 애플리케이션 등록 → 사용 API에 '데이터랩(검색어트렌드)', '데이터랩(쇼핑인사이트)' 추가.<br>**비워두면 가상 데이터로 시연**합니다.
CLIENT_ID = "" #@param {type:"string"}
CLIENT_SECRET = "" #@param {type:"string"}
데이터_종류 = "쇼핑인사이트(클릭량)" #@param ["쇼핑인사이트(클릭량)", "검색어트렌드(검색량)"]
쇼핑_카테고리 = "패션의류" #@param ["패션의류", "패션잡화"]
#@markdown **② 복종(키워드)** — 쉼표로 구분. 동의어는 `이름:키워드1|키워드2` (쇼핑인사이트는 첫 키워드만 사용)
복종_목록 = "코트, 패딩, 가죽자켓:가죽자켓|레더자켓, 점퍼, 니트, 블라우스, 티셔츠, 원피스" #@param {type:"string"}
성별 = "여성" #@param ["전체", "여성", "남성"]
연령대 = "전체" #@param ["전체", "20대", "30대", "40대", "50대", "20~30대", "30~40대", "40~50대"]
조회_기간_년 = 3 #@param {type:"slider", min:2, max:5, step:1}
예측_주수 = 12 #@param {type:"slider", min:4, max:26, step:1}
#@markdown **③ 판매수량 연계 (선택)** — 체크하면 주차별 판매 파일(엑셀/CSV, 열: `주차`, `복종`, `판매수량`)을 올려 판매수량까지 예측
판매데이터_업로드 = False #@param {type:"boolean"}
결과_엑셀_다운로드 = True #@param {type:"boolean"}

import datetime as dt
import json, os, subprocess, sys
import numpy as np
import pandas as pd
import requests

try:
    from IPython.display import display
except ImportError:
    display = print
try:
    import google.colab  # noqa: F401
    IN_COLAB = True
except ImportError:
    IN_COLAB = False

# ------------------------------------------------------------------ 0. 한글 폰트 (그래프용)
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm


def set_korean_font():
    cands = ["/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "C:/Windows/Fonts/malgun.ttf",
             "/System/Library/Fonts/AppleSDGothicNeo.ttc"]
    if IN_COLAB and not os.path.exists(cands[0]):
        subprocess.run("apt-get -qq install -y fonts-nanum > /dev/null", shell=True)
    for path in cands:
        if os.path.exists(path):
            fm.fontManager.addfont(path)
            plt.rcParams["font.family"] = fm.FontProperties(fname=path).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False


set_korean_font()

# ------------------------------------------------------------------ 1. 입력 정리
groups = []
for item in [s.strip() for s in 복종_목록.split(",") if s.strip()]:
    name, _, kws = item.partition(":")
    keywords = [k.strip() for k in (kws or name).split("|") if k.strip()]
    groups.append((name.strip(), keywords))
if len(groups) < 1:
    raise ValueError("복종_목록에 복종을 1개 이상 입력하세요.")

today = dt.date.today()
end_date = today - dt.timedelta(days=today.weekday() + 1)              # 지난주 일요일 (완료된 주까지만)
start_date = end_date - dt.timedelta(weeks=52 * 조회_기간_년) + dt.timedelta(days=1)  # 월요일 시작
SHOP = 데이터_종류.startswith("쇼핑")
GENDER = {"전체": "", "여성": "f", "남성": "m"}[성별]
AGE_DECADES = {"전체": [], "20대": [20], "30대": [30], "40대": [40], "50대": [50],
               "20~30대": [20, 30], "30~40대": [30, 40], "40~50대": [40, 50]}[연령대]
# 검색어트렌드 연령 코드: 3=19~24, 4=25~29, 5=30~34, 6=35~39, 7=40~44, 8=45~49, 9=50~54, 10=55~59
SEARCH_AGE = {20: ["3", "4"], 30: ["5", "6"], 40: ["7", "8"], 50: ["9", "10"]}
CATEGORY = {"패션의류": "50000000", "패션잡화": "50000001"}[쇼핑_카테고리]


# ------------------------------------------------------------------ 2. 네이버 데이터랩 수집
def call_naver(batch):
    """복종 최대 5개를 한 번에 조회 → {복종: Series(주차 → 지수)}. 지수는 이 요청 안에서 최댓값 100 기준."""
    headers = {"X-Naver-Client-Id": CLIENT_ID, "X-Naver-Client-Secret": CLIENT_SECRET,
               "Content-Type": "application/json"}
    body = {"startDate": start_date.isoformat(), "endDate": end_date.isoformat(), "timeUnit": "week"}
    if GENDER:
        body["gender"] = GENDER
    if SHOP:
        url = "https://openapi.naver.com/v1/datalab/shopping/category/keywords"
        body["category"] = CATEGORY
        body["keyword"] = [{"name": n, "param": kws[:1]} for n, kws in batch]
        if AGE_DECADES:
            body["ages"] = [str(a) for a in AGE_DECADES]
    else:
        url = "https://openapi.naver.com/v1/datalab/search"
        body["keywordGroups"] = [{"groupName": n, "keywords": kws[:20]} for n, kws in batch]
        if AGE_DECADES:
            body["ages"] = [c for a in AGE_DECADES for c in SEARCH_AGE[a]]
    res = requests.post(url, headers=headers, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), timeout=30)
    if res.status_code != 200:
        raise RuntimeError(f"네이버 API 오류 {res.status_code}: {res.text[:300]}\n"
                           "→ 키가 맞는지, 애플리케이션에 데이터랩 API가 추가돼 있는지 확인하세요.")
    out = {}
    for r in res.json()["results"]:
        s = pd.Series({pd.Timestamp(d["period"]) - pd.Timedelta(days=pd.Timestamp(d["period"]).weekday()): float(d["ratio"])
                       for d in r["data"]}, dtype=float)   # 주 시작(월요일)로 맞춤
        out[r["title"]] = s
    return out


def fetch_index():
    """5개씩 나눠 조회하고, 매 요청에 첫 복종(기준)을 넣어 요청 간 지수 크기를 맞춤."""
    anchor, rest = groups[0], groups[1:]
    batches = [[anchor] + rest[i:i + 4] for i in range(0, max(len(rest), 1), 4)]
    weeks = pd.date_range(pd.Timestamp(start_date), pd.Timestamp(end_date), freq="W-MON")
    frames, base = [], None
    for batch in batches:
        got = call_naver(batch)
        df = pd.DataFrame({n: got.get(n, pd.Series(dtype=float)) for n, _ in batch}).reindex(weeks).fillna(0.0)
        if base is None:
            base = df[anchor[0]].sum()
        else:
            scale = base / df[anchor[0]].sum() if df[anchor[0]].sum() > 0 else 1.0
            df = df * scale
            df = df.drop(columns=[anchor[0]])
        frames.append(df)
    idx = pd.concat(frames, axis=1)
    return idx * (100 / idx.values.max()) if idx.values.max() > 0 else idx


def demo_index():
    """API 키가 없을 때 쓰는 가상 지수 (복종별 계절 피크를 가정)."""
    weeks = pd.date_range(pd.Timestamp(start_date), pd.Timestamp(end_date), freq="W-MON")
    peak_week = {"코트": 46, "패딩": 49, "가죽자켓": 42, "점퍼": 43, "니트": 45, "블라우스": 14,
                 "티셔츠": 25, "원피스": 21, "셔츠": 15, "청바지": 38, "스커트": 18, "후드티": 41}
    rng = np.random.default_rng(7)
    data = {}
    for i, (name, _) in enumerate(groups):
        p = peak_week.get(name, (10 + 9 * i) % 52)
        w = weeks.isocalendar().week.values.astype(float)
        dist = np.minimum(np.abs(w - p), 52 - np.abs(w - p))
        season = np.exp(-(dist / 6.5) ** 2)
        trend = 1 + 0.12 * np.arange(len(weeks)) / 52 * (1 if i % 2 == 0 else -0.6)
        data[name] = (8 + 92 * season) * trend * rng.normal(1, 0.08, len(weeks))
    idx = pd.DataFrame(data, index=weeks).clip(lower=0)
    return idx * (100 / idx.values.max())


DEMO = not (CLIENT_ID.strip() and CLIENT_SECRET.strip())
if DEMO:
    print("⚠ API 키가 비어 있어 **가상 데이터**로 시연합니다. 실제 분석은 CLIENT_ID / CLIENT_SECRET을 입력하세요.")
    index = demo_index()
else:
    index = fetch_index()
src_label = "가상 데이터" if DEMO else f"네이버 데이터랩 {데이터_종류}"
print(f"수집: {src_label} | {index.index[0].date()} ~ {index.index[-1].date()} ({len(index)}주) | "
      f"성별 {성별} · 연령 {연령대} | 복종 {len(index.columns)}개 (최대값=100으로 통일)")


# ------------------------------------------------------------------ 3. 예측: 전년 동주 패턴 × 최근 성장률
def seasonal_forecast(s, horizon, recent=8):
    """미래 h주 = Σ(1·2년 전 같은 주 지수(3주 이동평균) × 해당 연도 대비 최근 8주 성장률) 평균."""
    s = s.astype(float)
    smooth = s.rolling(3, center=True, min_periods=1).mean()
    n = len(s)
    preds = np.zeros(horizon)
    for h in range(horizon):
        vals = []
        for y in (1, 2):
            lag = 52 * y
            pos = n + h - lag
            if pos < 0 or n - recent - lag < 0:
                continue
            past_recent = s.iloc[n - recent - lag:n - lag].sum()
            growth = s.iloc[n - recent:].sum() / past_recent if past_recent > 0 else 1.0
            vals.append(smooth.iloc[pos] * float(np.clip(growth, 0.3, 3.0)))
        preds[h] = np.mean(vals) if vals else s.iloc[-recent:].mean()
    future = pd.date_range(s.index[-1] + pd.Timedelta(weeks=1), periods=horizon, freq="W-MON")
    return pd.Series(np.clip(preds, 0, None), index=future)


def backtest(s, horizon):
    """마지막 h주를 가리고 예측 → WAPE(가중 절대오차율). 비교용으로 '최근 4주 평균 유지' 예측의 오차도 계산."""
    h = min(horizon, 8)
    train, test = s.iloc[:-h], s.iloc[-h:]
    f = seasonal_forecast(train, h).values
    naive = np.repeat(train.iloc[-4:].mean(), h)
    denom = test.abs().sum() or 1.0
    return np.abs(f - test.values).sum() / denom, np.abs(naive - test.values).sum() / denom


forecast = pd.DataFrame({c: seasonal_forecast(index[c], 예측_주수) for c in index.columns})

# ------------------------------------------------------------------ 4. 판매수량 연계 (선택)
sales = None
if 판매데이터_업로드:
    if IN_COLAB:
        from google.colab import files
        print("주차별 판매 파일을 선택하세요 (열: 주차, 복종, 판매수량)")
        up = files.upload()
        fname = list(up.keys())[0]
    else:
        fname = globals().get("SALES_FILE", "")
    raw = pd.read_csv(fname) if fname.lower().endswith(".csv") else pd.read_excel(fname)
    raw["주차"] = pd.to_datetime(raw["주차"])
    raw["주차"] = raw["주차"] - pd.to_timedelta(raw["주차"].dt.weekday, unit="D")   # 해당 주 월요일로 맞춤
    sales = raw.pivot_table(index="주차", columns="복종", values="판매수량", aggfunc="sum")
elif DEMO:
    # 시연용: 지수에 비례하는 가상 판매수량 (최근 1년)
    rng = np.random.default_rng(3)
    last_year = index.iloc[-52:]
    sales = (last_year * rng.uniform(20, 60, len(index.columns)) * rng.normal(1, 0.12, last_year.shape)).round()

links = {}
if sales is not None:
    for c in index.columns:
        if c not in sales.columns:
            continue
        best = None
        for lag in (0, 1):
            x = index[c].shift(lag)
            j = pd.concat([x.rename("x"), sales[c].rename("y")], axis=1).dropna()
            if len(j) < 8 or j["x"].std() == 0:
                continue
            b, a = np.polyfit(j["x"], j["y"], 1)
            r2 = np.corrcoef(j["x"], j["y"])[0, 1] ** 2
            if best is None or r2 > best["R²"]:
                best = {"lag": lag, "a": a, "b": b, "R²": r2, "주수": len(j)}
        if best:
            links[c] = best
    sales_fc = {}
    for c, m in links.items():
        x = pd.concat([index[c], forecast[c]]).shift(m["lag"]).loc[forecast.index]
        sales_fc[c] = (m["a"] + m["b"] * x).clip(lower=0).round()
    sales_fc = pd.DataFrame(sales_fc)

# ------------------------------------------------------------------ 5. 요약표
rows = []
for c in index.columns:
    s, f = index[c], forecast[c]
    recent4 = s.iloc[-4:].mean()
    ly4 = s.iloc[-56:-52].mean() if len(s) >= 56 else np.nan
    wape, naive_wape = backtest(s, 예측_주수)
    weekly = (f.iloc[-1] / f.iloc[0]) ** (1 / max(len(f) - 1, 1)) - 1 if f.iloc[0] > 0 and f.iloc[-1] > 0 else np.nan
    chg = f.mean() / recent4 - 1 if recent4 > 0 else np.nan
    row = {"복종": c, "최근4주 지수": recent4, "전년동기 대비": recent4 / ly4 - 1 if ly4 and ly4 > 0 else np.nan,
           f"향후{예측_주수}주 평균지수": f.mean(), "최근 대비 변화": chg,
           "예측 피크 주": f.idxmax().date(), "추세": "▲ 상승" if chg > 0.1 else ("▼ 하락" if chg < -0.1 else "― 유지"),
           "주평균 변화율": weekly, "검증오차(WAPE)": wape, "단순예측 오차": naive_wape}
    if c in links:
        row["판매연계 R²"] = links[c]["R²"]
        row[f"향후{예측_주수}주 예측판매(장)"] = sales_fc[c].sum()
    rows.append(row)
summary = pd.DataFrame(rows).set_index("복종").sort_values("최근 대비 변화", ascending=False)

fmt = {"최근4주 지수": "{:.1f}", "전년동기 대비": "{:+.0%}", f"향후{예측_주수}주 평균지수": "{:.1f}",
       "최근 대비 변화": "{:+.0%}", "주평균 변화율": "{:+.1%}", "검증오차(WAPE)": "{:.0%}", "단순예측 오차": "{:.0%}",
       "판매연계 R²": "{:.2f}", f"향후{예측_주수}주 예측판매(장)": "{:,.0f}"}
print(f"\n[복종별 판매추이 예측 요약] 기준: {src_label}, 향후 {예측_주수}주 (최근 대비 변화 큰 순)")
display(summary.style.format({k: v for k, v in fmt.items() if k in summary.columns}, na_rep="-")
        if display is not print else summary.round(3))
print("· 주평균 변화율 → '리오더·가격인하 손익분기 대시보드'의 [주간 판매 변화율]에 넣으면 시즌 잔여 수요에 반영됩니다.")
print("· 검증오차: 마지막 최대 8주를 가리고 맞춰본 오차. '단순예측 오차'(최근 4주 평균 유지)보다 작으면 계절 패턴이 유효합니다.")

# ------------------------------------------------------------------ 6. 그래프 (복종별: 판매수량 막대 + 지수 실적/예측 선)
n = len(index.columns)
cols = 3 if n > 4 else 2
rows_n = int(np.ceil(n / cols))
fig, axes = plt.subplots(rows_n, cols, figsize=(5.2 * cols, 3.3 * rows_n), squeeze=False)
show_from = index.index[-52]
for k, c in enumerate(index.columns):
    ax = axes[k // cols][k % cols]
    if sales is not None and c in sales.columns:
        sv = sales[c].loc[sales.index >= show_from]
        ax2 = ax.twinx()
        ax2.bar(sv.index, sv.values, width=5, color="#9DB8D6", alpha=0.7, label="판매수량")
        if c in links:
            ax2.bar(sales_fc.index, sales_fc[c].values, width=5, color="#9DB8D6", alpha=0.35, hatch="//",
                    label="예측 판매")
        ax2.set_ylabel("판매수량", fontsize=8)
        ax.set_zorder(ax2.get_zorder() + 1)
        ax.patch.set_visible(False)
    ax.plot(index[c].loc[show_from:].index, index[c].loc[show_from:].values, color="#E4572E", lw=1.8, label="지수(실적)")
    ax.plot(forecast.index, forecast[c].values, color="#E4572E", lw=1.8, ls="--", label="지수(예측)")
    ax.axvline(forecast.index[0], color="grey", lw=0.8, ls=":")
    chg_c = summary.loc[c, "최근 대비 변화"]
    ax.set_title(f"{c}  ({summary.loc[c, '추세']}" + (f", {chg_c:+.0%})" if pd.notna(chg_c) else ")"), fontsize=10)
    ax.tick_params(axis="x", labelsize=7, rotation=30)
    ax.set_ylabel("지수", fontsize=8)
    if k == 0:
        ax.legend(fontsize=7, loc="upper left")
for k in range(n, rows_n * cols):
    axes[k // cols][k % cols].axis("off")
fig.suptitle(f"복종별 최근 1년 추이와 향후 {예측_주수}주 예측 ({src_label})", fontsize=12)
fig.tight_layout()
plt.show()

if links:
    print("\n[주차별 예측 판매수량(장)]")
    display(sales_fc.T.rename(columns=lambda d: d.strftime("%m/%d")).astype(int))

# ------------------------------------------------------------------ 7. 엑셀 저장
if 결과_엑셀_다운로드:
    out = "복종별_판매추이예측.xlsx"
    with pd.ExcelWriter(out) as xw:
        summary.to_excel(xw, sheet_name="요약")
        forecast.round(2).rename(index=lambda d: d.date()).to_excel(xw, sheet_name="지수예측")
        index.round(2).rename(index=lambda d: d.date()).to_excel(xw, sheet_name="지수실적")
        if links:
            sales_fc.rename(index=lambda d: d.date()).to_excel(xw, sheet_name="판매예측")
            pd.DataFrame(links).T.to_excel(xw, sheet_name="판매연계식")
    print(f"\n엑셀 저장: {out}")
    if IN_COLAB:
        from google.colab import files
        files.download(out)
