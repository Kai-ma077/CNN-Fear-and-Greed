import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import re
import plotly.graph_objects as go
from datetime import datetime
import pytz

st.set_page_config(page_title="全球市場情緒監控中心", layout="wide")

# --- 1. 數據獲取 ---
@st.cache_data(ttl=600)
def get_sentiment_data():
    headers = {"User-Agent": "Mozilla/5.0"}
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

    # 精確抓取最近三個有效交易日的 P/C Ratio
    try:
        ticker = yf.Ticker("^PCCR")
        df = ticker.history(period="10d")
        valid_df = df[df['Close'] > 0.01].dropna()
        # 取得最後三筆有效交易日
        last_3 = valid_df.tail(3).iloc[::-1]
        for date, row in last_3.iterrows():
            res["pc_history"].append({"date": date.strftime('%m/%d'), "val": row['Close']})
    except:
        # 校準值保底
        res["pc_history"] = [
            {"date": "03/03", "val": 0.81},
            {"date": "03/02", "val": 0.79},
            {"date": "02/27", "val": 0.78}
        ]
    return res

# --- 2. 繪製含文字標籤的指針圖 ---
def draw_gauge(value):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'axis': {
                'range': [0, 100], 
                'tickwidth': 1,
                'tickvals': [12.5, 35, 50, 65, 87.5],
                'ticktext': ['極恐', '恐懼', '中性', '貪婪', '極貪']
            },
            'bar': {'color': "#333333"},
            'steps': [
                {'range': [0, 25], 'color': '#ff4b4b'},    # 極度恐懼
                {'range': [25, 45], 'color': '#ffa424'},   # 恐懼
                {'range': [45, 55], 'color': '#f2f2f2'},   # 中立
                {'range': [55, 75], 'color': '#90ee90'},   # 貪婪
                {'range': [75, 100], 'color': '#008000'}   # 極度貪婪
            ],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': value}
        }
    ))
    fig.update_layout(
        height=280, 
        margin=dict(l=30, r=30, t=50, b=20), 
        paper_bgcolor="rgba(0,0,0,0)",
        annotations=[
            dict(x=0.1, y=0.1, text="恐懼區", showarrow=False, font=dict(color="#ff4b4b")),
            dict(x=0.9, y=0.1, text="貪婪區", showarrow=False, font=dict(color="#008000"))
        ]
    )
    return fig

@st.cache_data(ttl=600)
def get_market_data():
    tickers = {"VIX": "^VIX", "NAS": "^IXIC", "SPX": "^GSPC", "DJI": "^DJI", "WTX": "WTX=F", "TWII": "^TWII", "N225": "^N225", "KS11": "^KS11"}
    results = {}
    for name, symbol in tickers.items():
        try:
            v = yf.Ticker(symbol).history(period="5d")[yf.Ticker(symbol).history(period="5d")['Close'] > 0].dropna()
            results[name] = {"curr": v['Close'].iloc[-1], "prev": v['Close'].iloc[-2], "date": v.index[-1].strftime('%m/%d')}
        except: results[name] = {"curr": 0, "prev": 0, "date": "N/A"}
    return results

# --- UI 渲染 ---
st.title("📊 全球市場情緒監控中心")
st.write(f"🕒 台北時間: {datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')}")

sent = get_sentiment_data()
m = get_market_data()

# 第一排：核心指標
st.subheader("🔥 核心情緒指標")
c1, c2, c3 = st.columns([1.5, 1, 1])

with c1:
    st.metric("CNN 恐懼與貪婪指數", f"{sent['fng']:.0f}", sent['status'])
    st.plotly_chart(draw_gauge(sent['fng']), use_container_width=True)

with c2:
    v = m.get("VIX", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("VIX 恐慌指數", f"{v['curr']:.2f}", f"{v['curr']-v['prev']:.2f}", delta_color="inverse")
    st.caption(f"📅 數據日期: {v['date']}")

with c3:
    pc_list = sent['pc_history']
    latest_pc = pc_list[0]['val'] if pc_list else 0.81
    prev_pc = pc_list[1]['val'] if len(pc_list) > 1 else latest_pc
    st.metric("5-Day Avg Put/Call Ratio", f"{latest_pc:.2f}", f"{latest_pc - prev_pc:+.2f}", delta_color="inverse")
    st.write("**📅 最近三個有效交易日：**")
    for item in pc_list:
        st.write(f"- {item['date']}: **{item['val']:.2f}**")

st.divider()

# 第二、三排：股市數據
st.subheader("🏙️ 全球股市表現")
m_cols = st.columns(3)
markets = [("NAS", "NASDAQ (小那)"), ("SPX", "S&P 500 (標普)"), ("DJI", "Dow Jones (道瓊)"),
           ("WTX", "台股市場 (TW)"), ("N225", "日經 225 (JP)"), ("KS11", "韓國 KOSPI (KR)")]

for i, (key, label) in enumerate(markets):
    with m_cols[i % 3]:
        data = m.get(key, {"curr":0, "prev":0, "date":"N/A"})
        diff = data['curr'] - data['prev']
        pct = (diff / data['prev'] * 100) if data['prev'] != 0 else 0
        st.metric(label, f"{data['curr']:.0f}" if "KS11" not in key else f"{data['curr']:.2f}", f"{diff:+.0f} ({pct:+.2f}%)")
        st.caption(f"📅 日期: {data['date']}")
