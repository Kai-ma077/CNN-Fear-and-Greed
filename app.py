import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(page_title="全球市場情緒監控中心", layout="wide")

# --- 1. 數據獲取 (全 API 模式，保證穩定) ---
@st.cache_data(ttl=300)
def get_stable_metrics():
    # 核心指標：VIX, PCCR(期權比), SPY(標普), QQQ(納指), DIA(道瓊), ^TWII(台股), ^N225(日經), ^KS11(韓股)
    tickers = {
        "VIX": "^VIX", "PCCR": "^PCCR", 
        "NAS": "^IXIC", "SPX": "^GSPC", "DJI": "^DJI", 
        "TW": "^TWII", "JP": "^N225", "KR": "^KS11"
    }
    
    results = {}
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            # 抓取 5 天日線確保有昨收價
            df = ticker.history(period="5d")
            if not df.empty:
                valid = df[df['Close'] > 0].dropna()
                curr = valid['Close'].iloc[-1]
                prev = valid['Close'].iloc[-2]
                
                # 時間標記邏輯
                last_dt = valid.index[-1]
                date_str = last_dt.strftime('%m/%d')
                
                # 亞股收盤時間人工標註
                if name == "TW": date_str += " 13:45"
                elif name == "JP": date_str += " 14:00"
                elif name == "KR": date_str += " 14:30"
                else: date_str += " 收盤"
                
                results[name] = {"curr": curr, "prev": prev, "date": date_str}
        except:
            results[name] = {"curr": 0, "prev": 0, "date": "N/A"}
    return results

# --- 2. 計算自定義恐懼貪婪值 ---
def calculate_custom_fng(vix, pccr):
    # 根據歷史區間估算一個情緒分數 (0-100)
    # VIX 越高越恐懼, PCCR 越高越恐懼
    vix_score = max(0, min(100, (40 - vix) * 2.5 + 25)) 
    pccr_score = max(0, min(100, (1.5 - pccr) * 100))
    combined = (vix_score + pccr_score) / 2
    
    if combined < 25: text = "極度恐懼"
    elif combined < 45: text = "恐懼"
    elif combined < 55: text = "中立"
    elif combined < 75: text = "貪婪"
    else: text = "極度貪婪"
    
    return int(combined), text

# --- UI 介面 ---
st.title("🌎 全球多空情緒監控中心")
st.write(f"🕒 系統檢查時間: {datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')}")

m = get_stable_metrics()
fng_val, fng_text = calculate_custom_fng(m['VIX']['curr'], m['PCCR']['curr'])

# 第一排：核心情緒指標
st.subheader("🔥 核心情緒指標")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("情緒診斷 (基於 VIX+PCCR)", f"{fng_val}", fng_text)
    st.progress(fng_val)
    st.caption("註：因 CNN 封鎖，此為根據波動率與期權比率計算之實質情緒")
with c2:
    v = m['VIX']
    st.metric("VIX 恐慌指數", f"{v['curr']:.2f}", f"{v['curr']-v['prev']:.2f}", delta_color="inverse")
    st.caption(f"📅 數據時間: {v['date']}")
with c3:
    pc = m['PCCR']
    st.metric("CBOE Put/Call Ratio", f"{pc['curr']:.2f}", f"{pc['curr']-pc['prev']:.2f}", delta_color="inverse")
    st.caption(f"📅 數據時間: {pc['date']}")

st.divider()

# 第二排：美股市場 (小那 -> 標普 -> 道瓊)
st.subheader("🏙️ 美股市場")
cu1, cu2, cu3 = st.columns(3)
with cu1:
    n = m['NAS']
    st.metric("NASDAQ (小那)", f"{n['curr']:.0f}", f"{((n['curr']-n['prev'])/n['prev'])*100 if n['prev']!=0 else 0:.2f}%")
with cu2:
    s = m['SPX']
    st.metric("S&P 500 (標普)", f"{s['curr']:.0f}", f"{((s['curr']-s['prev'])/s['prev'])*100 if s['prev']!=0 else 0:.2f}%")
with cu3:
    d = m['DJI']
    st.metric("Dow Jones (道瓊)", f"{d['curr']:.0f}", f"{((d['curr']-d['prev'])/d['prev'])*100 if d['prev']!=0 else 0:.2f}%")

# 第三排：亞股市場 (台股第一)
st.subheader("🗾 亞股市場")
ca1, ca2, ca3 = st.columns(3)
with ca1:
    tw = m['TW']
    diff = tw['curr'] - tw['prev']
    pct = (diff / tw['prev']) * 100 if tw['prev'] != 0 else 0
    st.metric("台股加權 (TW)", f"{tw['curr']:.0f}", f"{diff:+.0f} ({pct:+.2f}%)")
    st.caption(f"📅 收盤時間: {tw['date']}")
with ca2:
    nk = m['JP']
    st.metric("日經 225 (JP)", f"{nk['curr']:.0f}", f"{((nk['curr']-nk['prev'])/nk['prev'])*100 if nk['prev']!=0 else 0:.2f}%")
    st.caption(f"📅 收盤時間: {nk['date']}")
with ca3:
    ks = m['KR']
    st.metric("韓國 KOSPI (KR)", f"{ks['curr']:.2f}", f"{((ks['curr']-ks['prev'])/ks['prev'])*100 if ks['prev']!=0 else 0:.2f}%")
    st.caption(f"📅 收盤時間: {ks['date']}")
