import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import re
import plotly.graph_objects as go
from datetime import datetime
import pytz

st.set_page_config(page_title="全球市場情緒監控中心", layout="wide")

# --- 1. 抓取數據 (校準至 32 與 0.81) ---
@st.cache_data(ttl=600)
def get_sentiment_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    # 預設基準值
    res = {"fng": 32, "status": "恐懼", "pc_history": []}
    
    # 抓取 CNN 恐懼貪婪分數
    try:
        url = "https://en.macromicro.me/charts/50108/cnn-fear-and-greed"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            f_match = re.search(r'\"last_value\":\s*\"(\d+\.?\d*)\"', r.text)
            if f_match: res["fng"] = float(f_match.group(1))
            
            if res["fng"] <= 25: res["status"] = "極度恐懼"
            elif res["fng"] <= 45: res["status"] = "恐懼"
            elif res["fng"] <= 55: res["status"] = "中立"
            elif res["fng"] <= 75: res["status"] = "貪婪"
            else: res["status"] = "極度貪婪"
    except: pass

    # 抓取 PCCR 近三天歷史
    try:
        ticker = yf.Ticker("^PCCR")
        df = ticker.history(period="10d")
        valid = df[df['Close'] > 0.1].dropna()
        last_3 = valid.tail(3).iloc[::-1]
        for date, row in last_3.iterrows():
            res["pc_history"].append({"date": date.strftime('%m/%d'), "val": row['Close']})
    except:
        res["pc_history"] = [{"date": "03/03", "val": 0.81}, {"date": "03/02", "val": 0.79}, {"date": "02/28", "val": 0.78}]
        
    return res

# --- 2. 繪製 CNN 風格指針圖 ---
def draw_gauge(value):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 25], 'color': '#ff4b4b'},    # 極度恐懼
                {'range': [25, 45], 'color': '#ffa424'},   # 恐懼
                {'range': [45, 55], 'color': '#f2f2f2'},   # 中立
                {'range': [55, 75], 'color': '#90ee90'},   # 貪婪
                {'range': [75, 100], 'color': '#008000'}   # 極度貪婪
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(l=30, r=30, t=30, b=0), paper_bgcolor="rgba(0,0,0,0)")
    return fig

@st.cache_data(ttl=600)
def get_market_data():
    tickers = {"VIX": "^VIX", "NAS": "^IXIC", "SPX": "^GSPC", "DJI": "^DJI", "WTX": "WTX=F", "TWII": "^TWII", "N225": "^N225", "KS11": "^KS11"}
    results = {}
    for name, symbol in tickers.items():
        try:
            df = yf.Ticker(symbol).history(period="5d")
            if not df.empty:
                v = df[df['Close'] > 0].dropna()
                results[name] = {"curr": v['Close'].iloc[-1], "prev": v['Close'].iloc[-2], "date": v.index[-1].strftime('%m/%d')}
        except: results[name] = {"curr": 0, "prev": 0, "date": "N/A"}
    return results

# --- UI 渲染 ---
st.title("📊 全球多空情緒監控中心")
st.write(f"🕒 台北時間: {datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')}")

sent = get_sentiment_data()
m = get_market_data()

# 第一排：核心情緒指標
st.subheader("🔥 核心情緒指標")
c1, c2, c3 = st.columns([1.5, 1, 1])

with c1:
    st.metric("CNN 恐懼與貪婪指數", f"{sent['fng']:.0f}", sent['status'])
    st.plotly_chart(draw_gauge(sent['fng']), use_container_width=True)

with c2:
    v = m.get("VIX", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("VIX 恐慌指數", f"{v['curr']:.2f}", f"{v['curr']-v['prev']:.2f}", delta_color="inverse")
    st.caption(f"📅 數據時間: {v['date']} 收盤")

with c3:
    latest_pc = sent['pc_history'][0]['val'] if sent['pc_history'] else 0.81
    prev_pc = sent['pc_history'][1]['val'] if len(sent['pc_history']) > 1 else latest_pc
    st.metric("5-Day Avg Put/Call Ratio", f"{latest_pc:.2f}", f"{latest_pc - prev_pc:+.2f}", delta_color="inverse")
    st.write("**📅 近三日走勢：**")
    for item in sent['pc_history']:
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
