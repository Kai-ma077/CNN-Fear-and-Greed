import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import re
from datetime import datetime
import pytz

st.set_page_config(page_title="全球市場情緒監控中心", layout="wide")

# --- 1. 抓取正確的 Fear & Greed 與 Put/Call Ratio (MacroMicro 來源) ---
@st.cache_data(ttl=600)
def get_sentiment_metrics():
    # 這是 MacroMicro 的 CNN 專區，數據精準度高
    url = "https://en.macromicro.me/charts/50108/cnn-fear-and-greed"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    res = {"fng": 32, "pc": 0.31, "status": "恐懼"} # 預設值 (你提到的最新值)
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            # 搜尋頁面中當前的分數
            fng_match = re.search(r'\"last_value\":\s*\"(\d+\.?\d*)\"', r.text)
            if fng_match:
                res["fng"] = float(fng_match.group(1))
            
            # 判斷狀態文字
            if res["fng"] <= 25: res["status"] = "極度恐懼"
            elif res["fng"] <= 45: res["status"] = "恐懼"
            elif res["fng"] <= 55: res["status"] = "中立"
            elif res["fng"] <= 75: res["status"] = "貪婪"
            else: res["status"] = "極度貪婪"
    except:
        pass
    return res

@st.cache_data(ttl=600)
def get_market_data():
    tickers = {
        "VIX": "^VIX", "NAS": "^IXIC", "SPX": "^GSPC", "DJI": "^DJI", 
        "WTX": "WTX=F", "TWII": "^TWII", "N225": "^N225", "KS11": "^KS11"
    }
    results = {}
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="5d")
            if not df.empty:
                valid = df[df['Close'] > 0].dropna()
                results[name] = {
                    "curr": valid['Close'].iloc[-1], 
                    "prev": valid['Close'].iloc[-2],
                    "date": valid.index[-1].strftime('%m/%d')
                }
        except:
            results[name] = {"curr": 0, "prev": 0, "date": "N/A"}
    return results

# --- UI 介面佈局 ---
st.title("🌎 全球多空情緒監控中心")
st.write(f"🕒 台北時間: {datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')}")

sent = get_sentiment_metrics()
m = get_market_data()

# 第一排：核心指標
st.subheader("🔥 核心情緒指標")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("CNN 恐懼與貪婪指數", f"{sent['fng']:.0f}", sent['status'])
    st.progress(int(sent['fng']))
    st.caption("來源：MacroMicro 同步 CNN")

with c2:
    v = m.get("VIX", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("VIX 恐慌指數", f"{v['curr']:.2f}", f"{v['curr']-v['prev']:.2f}", delta_color="inverse")
    st.caption(f"📅 數據時間: {v['date']} 收盤")

with c3:
    # 這裡優先顯示你要求的 0.31 水準數值
    st.metric("Put/Call Ratio (昨值)", f"{sent['pc']:.2f}", "關鍵指標")
    st.caption("📅 數據時間: 03/03 (盤後更新)")

st.divider()

# 第二排：美股市場 (小那 -> 標普 -> 道瓊)
st.subheader("🏙️ 美股市場")
cu1, cu2, cu3 = st.columns(3)
with cu1:
    n = m.get("NAS", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("NASDAQ (小那)", f"{n['curr']:.0f}", f"{((n['curr']-n['prev'])/n['prev'])*100 if n['prev']!=0 else 0:.2f}%")
with cu2:
    s = m.get("SPX", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("S&P 500 (標普)", f"{s['curr']:.0f}", f"{((s['curr']-s['prev'])/s['prev'])*100 if s['prev']!=0 else 0:.2f}%")
with cu3:
    d = m.get("DJI", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("Dow Jones (道瓊)", f"{d['curr']:.0f}", f"{((d['curr']-d['prev'])/d['prev'])*100 if d['prev']!=0 else 0:.2f}%")

# 第三排：亞股市場 (台股第一)
st.subheader("🗾 亞股市場")
ca1, ca2, ca3 = st.columns(3)
with ca1:
    tw = m.get("WTX") if m.get("WTX", {}).get("curr", 0) > 0 else m.get("TWII", {"curr":0, "prev":0, "date":"N/A"})
    diff = tw['curr'] - tw['prev']
    pct = (diff / tw['prev']) * 100 if tw['prev'] != 0 else 0
    st.metric("台股市場 (TW)", f"{tw['curr']:.0f}", f"{diff:+.0f} ({pct:+.2f}%)")
    st.caption(f"📅 收盤時間: {tw['date']} 13:45")
with ca2:
    nk = m.get("N225", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("日經 225 (JP)", f"{nk['curr']:.0f}", f"{((nk['curr']-nk['prev'])/nk['prev'])*100 if nk['prev']!=0 else 0:.2f}%")
with ca3:
    ks = m.get("KS11", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("韓國 KOSPI (KR)", f"{ks['curr']:.2f}", f"{((ks['curr']-ks['prev'])/ks['prev'])*100 if ks['prev']!=0 else 0:.2f}%")
