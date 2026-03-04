import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import re
from datetime import datetime
import pytz

st.set_page_config(page_title="全球市場情緒監控中心", layout="wide")

# --- 1. 定義數據抓取邏輯 (強化版 Fear & Greed) ---
@st.cache_data(ttl=600)
def get_fng_data():
    # 策略：先抓玩股網，失敗則回傳預設值
    url = "https://www.wantgoo.com/global/macroeconomics/fearandgreed"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/"
    }
    try:
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code == 200:
            # 尋找頁面中像是 "32" 或 "45" 的關鍵分數
            # 優先找數字，再找狀態文字
            scores = re.findall(r'(\d+)', re.search(r'當日.*?(\d+)', r.text).group(0)) if "當日" in r.text else []
            if not scores:
                scores = re.findall(r'\"y\":(\d+)', r.text) # 找圖表數據
            
            score = int(scores[0]) if scores else 50
            
            # 定義狀態標籤
            if score <= 25: text = "極度恐懼"
            elif score <= 45: text = "恐懼"
            elif score <= 55: text = "中立"
            elif score <= 75: text = "貪婪"
            else: text = "極度貪婪"
            
            return {"val": score, "text": text, "success": True}
        return {"val": 50, "text": "連線受限", "success": False}
    except:
        return {"val": 50, "text": "數據維護中", "success": False}

@st.cache_data(ttl=600)
def get_market_data():
    tickers = {
        "VIX": "^VIX", "PCCR": "^PCCR", "NAS": "^IXIC", "SPX": "^GSPC", "DJI": "^DJI", 
        "WTX": "WTX=F", "TWII": "^TWII", "N225": "^N225", "KS11": "^KS11"
    }
    results = {}
    for name, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="5d")
            if not df.empty:
                valid = df[df['Close'] > 0].dropna()
                curr = valid['Close'].iloc[-1]
                prev = valid['Close'].iloc[-2]
                
                # 精確時間處理
                last_dt = valid.index[-1]
                time_label = last_dt.strftime('%m/%d')
                
                # 亞股特殊標註收盤時間
                if name == "WTX" or name == "TWII": time_label += " 13:45"
                elif name == "N225": time_label += " 14:00"
                elif name == "KS11": time_label += " 14:30"
                else: time_label += " 收盤"
                
                results[name] = {"curr": curr, "prev": prev, "date": time_label}
        except:
            results[name] = {"curr": 0, "prev": 0, "date": "N/A"}
    return results

# --- UI 介面 ---
st.title("🌎 全球多空情緒監控中心")
st.write(f"🕒 系統檢查時間: {datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')}")

fng = get_fng_data()
m_data = get_market_data()

# 第一排：核心情緒指標
st.subheader("🔥 核心情緒指標")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("恐懼與貪婪指數", f"{fng['val']}", fng['text'])
    st.progress(fng['val'])
    if not fng['success']:
        st.caption("⚠️ 外部源連線不穩，顯示為預設值")
with c2:
    v = m_data.get("VIX", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("VIX 恐慌指數", f"{v['curr']:.2f}", f"{v['curr']-v['prev']:.2f}", delta_color="inverse")
    st.caption(f"📅 數據時間: {v['date']}")
with c3:
    pc = m_data.get("PCCR", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("CBOE Put/Call Ratio", f"{pc['curr']:.2f}", f"{pc['curr']-pc['prev']:.2f}", delta_color="inverse")
    st.caption(f"📅 數據時間: {pc['date']}")

st.divider()

# 第二排：美股市場 (排序：小那 -> 標普 -> 道瓊)
st.subheader("🏙️ 美股市場")
cu1, cu2, cu3 = st.columns(3)
with cu1:
    n = m_data.get("NAS", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("NASDAQ (小那)", f"{n['curr']:.0f}", f"{((n['curr']-n['prev'])/n['prev'])*100 if n['prev']!=0 else 0:.2f}%")
with cu2:
    s = m_data.get("SPX", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("S&P 500 (標普)", f"{s['curr']:.0f}", f"{((s['curr']-s['prev'])/s['prev'])*100 if s['prev']!=0 else 0:.2f}%")
with cu3:
    d = m_data.get("DJI", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("Dow Jones (道瓊)", f"{d['curr']:.0f}", f"{((d['curr']-d['prev'])/d['prev'])*100 if d['prev']!=0 else 0:.2f}%")

# 第三排：亞股市場 (台股第一)
st.subheader("🗾 亞股市場")
ca1, ca2, ca3 = st.columns(3)
with ca1:
    # 台指期/加權 自動備援
    tw = m_data.get("WTX") if m_data.get("WTX", {}).get("curr", 0) > 0 else m_data.get("TWII", {"curr":0, "prev":0, "date":"N/A"})
    diff = tw['curr'] - tw['prev']
    pct = (diff / tw['prev']) * 100 if tw['prev'] != 0 else 0
    st.metric("台股市場 (TW)", f"{tw['curr']:.0f}", f"{diff:+.0f} ({pct:+.2f}%)")
    st.caption(f"📅 時間: {tw['date']}")
with ca2:
    nk = m_data.get("N225", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("日經 225 (JP)", f"{nk['curr']:.0f}", f"{((nk['curr']-nk['prev'])/nk['prev'])*100 if nk['prev']!=0 else 0:.2f}%")
    st.caption(f"📅 時間: {nk['date']}")
with ca3:
    ks = m_data.get("KS11", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("韓國 KOSPI (KR)", f"{ks['curr']:.2f}", f"{((ks['curr']-ks['prev'])/ks['prev'])*100 if ks['prev']!=0 else 0:.2f}%")
    st.caption(f"📅 時間: {ks['date']}")

st.divider()
st.caption("數據來源: Yahoo Finance & WantGoo | 若恐懼指數失敗請以 VIX 為主")
