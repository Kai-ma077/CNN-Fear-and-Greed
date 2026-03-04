import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="全球市場情緒監控中心", layout="wide")

@st.cache_data(ttl=600)
def get_cnn_fng():
    url = "https://production.dataviz.cnn.io/index/feargreed/static/data"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Origin": "https://www.cnn.com",
        "Referer": "https://www.cnn.com/markets/fear-and-greed"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            score = data['market_rating_current']['score']
            rating = data['market_rating_current']['rating']
            return {"val": float(score), "text": rating.upper()}
        return None
    except:
        return None

@st.cache_data(ttl=600)
def get_global_market():
    # 包含道瓊與亞股的新 Ticker 清單
    tickers = {
        "VIX 恐慌指數": "^VIX",
        "Put/Call Ratio": "^PCCR",
        "納斯達克 (US)": "^IXIC",
        "標普 500 (US)": "^GSPC",
        "道瓊工業 (US)": "^DJI",
        "台灣加權指數 (TW)": "^TWII",
        "日經 225 (JP)": "^N225",
        "韓國綜合 (KR)": "^KS11"
    }
    results = {}
    for name, symbol in tickers.items():
        try:
            data = yf.Ticker(symbol).history(period="15d")
            if not data.empty:
                valid_data = data[data['Close'] > 0].dropna()
                curr = valid_data['Close'].iloc[-1]
                prev = valid_data['Close'].iloc[-2]
                results[name] = {"curr": curr, "prev": prev}
        except:
            results[name] = {"curr": 0, "prev": 0}
    return results

st.title("🌎 全球多空情緒監控中心")
st.write(f"最後更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (台北時間)")

# 獲取數據
fng = get_cnn_fng()
data = get_global_market()

# --- 第一排：核心情緒指標 ---
st.subheader("🔥 核心情緒指標")
c1, c2, c3 = st.columns(3)

with c1:
    if fng:
        st.metric("CNN 恐懼與貪婪指數", f"{fng['val']:.0f}", fng['text'])
        st.progress(int(fng['val']))
    else:
        st.metric("CNN 恐懼與貪婪", "數據更新中", "請稍後再試")

with c2:
    v = data.get("VIX 恐慌指數", {"curr":0, "prev":0})
    st.metric("VIX 恐慌指數", f"{v['curr']:.2f}", f"{v['curr']-v['prev']:.2f}", delta_color="inverse")
    
with c3:
    pc = data.get("Put/Call Ratio", {"curr":0, "prev":0})
    if pc['curr'] > 0:
        st.metric("CBOE Put/Call Ratio", f"{pc['curr']:.2f}", f"{pc['curr']-pc['prev']:.2f}", delta_color="inverse")
    else:
        st.metric("CBOE Put/Call Ratio", "結算中", "無昨值")

st.divider()

# --- 第二排：美股市場 (排序：納斯達克 -> 標普 -> 道瓊) ---
st.subheader("🏙️ 美股市場")
cus1, cus2, cus3 = st.columns(3)

with cus1:
    nas = data.get("納斯達克 (US)", {"curr":0, "prev":0})
    nas_pct = ((nas['curr']-nas['prev'])/nas['prev'])*100 if nas['prev']!=0 else 0
    st.metric("NASDAQ (小那)", f"{nas['curr']:.0f}", f"{nas_pct:.2f}%")

with cus2:
    sp = data.get("標普 500 (US)", {"curr":0, "prev":0})
    sp_pct = ((sp['curr']-sp['prev'])/sp['prev'])*100 if sp['prev']!=0 else 0
    st.metric("S&P 500 (標普)", f"{sp['curr']:.0f}", f"{sp_pct:.2f}%")

with cus3:
    dji = data.get("道瓊工業 (US)", {"curr":0, "prev":0})
    dji_pct = ((dji['curr']-dji['prev'])/dji['prev'])*100 if dji['prev']!=0 else 0
    st.metric("Dow Jones (道瓊)", f"{dji['curr']:.0f}", f"{dji_pct:.2f}%")

# --- 第三排：亞股市場 (台股第一) ---
st.subheader("🗾 亞股市場")
cas1, cas2, cas3 = st.columns(3)
with cas1:
    tw = data.get("台灣加權指數 (TW)", {"curr":0, "prev":0})
    st.metric("台股加權 (TW)", f"{tw['curr']:.0f}", f"{tw['curr']-tw['prev']:.2f}")
with cas2:
    nk = data.get("日經 225 (JP)", {"curr":0, "prev":0})
    nk_pct = ((nk['curr']-nk['prev'])/nk['prev'])*100 if nk['prev']!=0 else 0
    st.metric("日經 225 (JP)", f"{nk['curr']:.0f}", f"{nk_pct:.2f}%")
with cas3:
    ks = data.get("韓國綜合 (KR)", {"curr":0, "prev":0})
    ks_pct = ((ks['curr']-ks['prev'])/ks['prev'])*100 if ks['prev']!=0 else 0
    st.metric("韓國 KOSPI (KR)", f"{ks['curr']:.2f}", f"{ks_pct:.2f}%")

st.divider()
st.caption("數據來源：Yahoo Finance & CNN Business (美股指數由 API 即時供應)")
