import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import re
from datetime import datetime
import pytz

st.set_page_config(page_title="全球市場情緒監控中心", layout="wide")

@st.cache_data(ttl=600)
def get_fng_data():
    # 抓取 CNN 恐懼貪婪指數 (透過 MacroMicro 鏡像)
    url = "https://en.macromicro.me/charts/50108/cnn-fear-and-greed"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = {"fng": 32, "status": "恐懼"} 
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            fng_match = re.search(r'\"last_value\":\s*\"(\d+\.?\d*)\"', r.text)
            if fng_match:
                res["fng"] = float(fng_match.group(1))
            if res["fng"] <= 25: res["status"] = "極度恐懼"
            elif res["fng"] <= 45: res["status"] = "恐懼"
            elif res["fng"] <= 55: res["status"] = "中立"
            elif res["fng"] <= 75: res["status"] = "貪婪"
            else: res["status"] = "極度貪婪"
    except: pass
    return res

@st.cache_data(ttl=600)
def get_pc_one_week():
    # 抓取 CBOE Put/Call Ratio 指數近一週 (5個交易日) 的數據
    try:
        ticker = yf.Ticker("^PCCR")
        df = ticker.history(period="15d") # 抓多一點確保扣除假日有5天
        valid = df[df['Close'] > 0.1].dropna() 
        # 取得最後 5 筆 (近一週交易日)
        last_5 = valid.tail(5).iloc[::-1] 
        pc_list = []
        for date, row in last_5.iterrows():
            pc_list.append({
                "date": date.strftime('%m/%d'),
                "val": round(row['Close'], 2)
            })
        return pc_list
    except:
        return [{"date": "N/A", "val": 0.31}]

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
                v = df[df['Close'] > 0].dropna()
                results[name] = {"curr": v['Close'].iloc[-1], "prev": v['Close'].iloc[-2], "date": v.index[-1].strftime('%m/%d')}
        except: results[name] = {"curr": 0, "prev": 0, "date": "N/A"}
    return results

# --- UI 介面 ---
st.title("🌎 全球多空情緒監控中心")
st.write(f"🕒 台北時間: {datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')}")

fng = get_fng_data()
pc_history = get_pc_one_week()
m = get_market_data()

# 第一排：核心情緒指標
st.subheader("🔥 核心情緒指標")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("CNN 恐懼與貪婪指數", f"{fng['fng']:.0f}", fng['status'])
    st.progress(int(fng['fng']))
    st.caption("來源：MacroMicro 同步 CNN")

with c2:
    v = m.get("VIX", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("VIX 恐慌指數", f"{v['curr']:.2f}", f"{v['curr']-v['prev']:.2f}", delta_color="inverse")
    st.caption(f"📅 數據時間: {v['date']} 收盤")

with c3:
    # 顯示最新 P/C Ratio 與漲跌
    latest_pc = pc_history[0]['val'] if pc_history else 0
    prev_pc = pc_history[1]['val'] if len(pc_history) > 1 else latest_pc
    st.metric("Put/Call Ratio (最新)", f"{latest_pc:.2f}", f"{latest_pc - prev_pc:+.2f}", delta_color="inverse")
    
    # 顯示一週列表
    st.write("**📅 近一週走勢 (最新在首)：**")
    for item in pc_history:
        st.write(f"- {item['date']}: **{item['val']:.2f}**")

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
    diff, pct = tw['curr']-tw['prev'], ((tw['curr']-tw['prev'])/tw['prev'])*100 if tw['prev']!=0 else 0
    st.metric("台股市場 (TW)", f"{tw['curr']:.0f}", f"{diff:+.0f} ({pct:+.2f}%)")
    st.caption(f"📅 收盤: {tw['date']} 13:45")
with ca2:
    nk = m.get("N225", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("日經 225 (JP)", f"{nk['curr']:.0f}", f"{((nk['curr']-nk['prev'])/nk['prev'])*100 if nk['prev']!=0 else 0:.2f}%")
with ca3:
    ks = m.get("KS11", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("韓國 KOSPI (KR)", f"{ks['curr']:.2f}", f"{((ks['curr']-ks['prev'])/ks['prev'])*100 if ks['prev']!=0 else 0:.2f}%")
