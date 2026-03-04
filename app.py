import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import re
from datetime import datetime

st.set_page_config(page_title="全球市場情緒監控中心", layout="wide")

@st.cache_data(ttl=600)
def get_cnn_fng():
    # 嘗試抓取 CNN 真正的資料接口
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
            # 取得 CNN 當前的數據
            score = data['market_rating_current']['score']
            rating = data['market_rating_current']['rating']
            return {"val": float(score), "text": rating.upper()}
        return None
    except:
        return None

@st.cache_data(ttl=600)
def get_global_market():
    tickers = {
        "VIX 恐慌指數": "^VIX",
        "Put/Call Ratio": "^PCCR",
        "標普 500 (US)": "^GSPC",
        "納斯達克 (US)": "^IXIC",
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
        st.metric("CNN 恐懼與貪婪", "連線受限", "請手動檢查官網")
        st.info("註：CNN 伺服器頻繁封鎖雲端 IP，建議觀察 VIX 作為主要指標。")

with c2:
    v = data.get("VIX 恐慌指數", {"curr":0, "prev":0})
    st.metric("VIX 恐慌指數", f"{v['curr']:.2f}", f"{v['curr']-v['prev']:.2f}", delta_color="inverse")
    
with c3:
    pc = data.get("Put/Call Ratio", {"curr":0, "prev":0})
    if pc['curr'] > 0:
        st.metric("CBOE Put/Call Ratio", f"{pc['curr']:.2f}", f"{pc['curr']-pc['prev']:.2f}", delta_color="inverse")
    else:
        st.metric("CBOE Put/Call Ratio", "結算中", "無資料")

st.divider()

# --- 第二排：美股市場 ---
st.subheader("🏙️ 美股市場")
c_us1, c_us2 = st.columns(2)
with c_us1:
    sp = data.get("標普 500 (US)", {"curr":0, "prev":0})
    pct = ((sp['curr']-sp['prev'])/sp['prev'])*100 if sp['prev']!=0 else 0
    st.metric("S&P 500", f"{sp['curr']:.0f}", f"{pct:.2f}%")
with c_us2:
    nas = data.get("納斯達克 (US)", {"curr":0, "prev":0})
    pct = ((nas['curr']-nas['prev'])/nas['prev'])*100 if nas['prev']!=0 else 0
    st.metric("NASDAQ", f"{nas['curr']:.0f}", f"{pct:.2f}%")

# --- 第三排：亞股市場 (台股第一) ---
st.subheader("🗾 亞股市場")
c_as1, c_as2, c_as3 = st.columns(3)
with c_as1:
    tw = data.get("台灣加權指數 (TW)", {"curr":0, "prev":0})
    st.metric("台股加權 (TW)", f"{tw['curr']:.0f}", f"{tw['curr']-tw['prev']:.2f}")
with c_as2:
    nk = data.get("日經 225 (JP)", {"curr":0, "prev":0})
    pct = ((nk['curr']-nk['prev'])/nk['prev'])*100 if nk['prev']!=0 else 0
    st.metric("日經 225 (JP)", f"{nk['curr']:.0f}", f"{pct:.2f}%")
with c_as3:
    ks = data.get("韓國綜合 (KR)", {"curr":0, "prev":0})
    pct = ((ks['curr']-ks['prev'])/ks['prev'])*100 if ks['prev']!=0 else 0
    st.metric("韓國 KOSPI (KR)", f"{ks['curr']:.2f}", f"{pct:.2f}%")

st.caption("數據來源：Yahoo Finance & CNN Business (若 CNN 數據未顯示代表 API 暫時被封鎖)")
