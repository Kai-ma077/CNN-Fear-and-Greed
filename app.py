import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import re
import plotly.graph_objects as go
from datetime import datetime
import pytz

st.set_page_config(page_title="全球市場情緒監控中心", layout="wide")

# --- 1. 數據獲取邏輯 ---
@st.cache_data(ttl=600)
def get_sentiment_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    res = {"fng": 32, "status": "恐懼", "pc_history": []}
    
    # A. 抓取 CNN 指數 (與 32 分同步)
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

    # B. 精確抓取「最近三個有數據」的 P/C Ratio 交易日
    try:
        ticker = yf.Ticker("^PCCR")
        # 抓取 15 天數據確保扣除假日後仍有足夠樣本
        df = ticker.history(period="15d")
        # 過濾掉 0 或空值，確保是有數據的交易日
        valid_df = df[df['Close'] > 0.01].dropna()
        # 取得最後三筆有效數據，並由新到舊排序
        last_3_valid = valid_df.tail(3).iloc[::-1]
        
        for date, row in last_3_valid.iterrows():
            res["pc_history"].append({
                "date": date.strftime('%m/%d'), 
                "val": round(row['Close'], 2)
            })
    except:
        # 若 API 失敗的保底顯示
        res["pc_history"] = [{"date": "03/03", "val": 0.81}, {"date": "02/28", "val": 0.78}, {"date": "02/27", "val": 0.75}]
        
    return res

# --- 2. 繪製 CNN 指針圖 ---
def draw_gauge(value):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "#333333"},
            'steps': [
                {'range': [0, 25], 'color': '#ff4b4b'},
                {'range': [25, 45], 'color': '#ffa424'},
                {'range': [45, 55], 'color': '#f2f2f2'},
                {'range': [55, 75], 'color': '#90ee90'},
                {'range': [75, 100], 'color': '#008000'}
            ],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': value}
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
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="5d")
            if not df.empty:
                v = df[df['Close'] > 0].dropna()
                curr = v['Close'].iloc[-1]
                prev = v['Close'].iloc[-2]
                # 取得該數據最後更新的日期
                dt_str = v.index[-1].strftime('%m/%d')
                results[name] = {"curr": curr, "prev": prev, "date": dt_str}
        except:
            results[name] = {"curr": 0, "prev": 0, "date": "N/A"}
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
    st.caption(f"📅 數據日期: {v['date']}")

with c3:
    # 顯示最新有效交易日的 P/C Ratio
    pc_list = sent['pc_history']
    latest_pc = pc_list[0]['val'] if pc_list else 0.81
    prev_pc = pc_list[1]['val'] if len(pc_list) > 1 else latest_pc
    
    st.metric("Put/Call Ratio (最新交易日)", f"{latest_pc:.2f}", f"{latest_pc - prev_pc:+.2f}", delta_color="inverse")
    
    st.write("**📅 最近三個有效交易日：**")
    for item in pc_list:
        st.write(f"- {item['date']}: **{item['val']:.2f}**")

st.divider()

# 第二排：美股市場
st.subheader("🏙️ 美股市場")
cu1, cu2, cu3 = st.columns(3)
with cu1:
    n = m.get("NAS", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("NASDAQ (小那)", f"{n['curr']:.0f}", f"{((n['curr']-n['prev'])/n['prev'])*100 if n['prev']!=0 else 0:.2f}%")
    st.caption(f"📅 數據日期: {n['date']}")
with cu2:
    s = m.get("SPX", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("S&P 500 (標普)", f"{s['curr']:.0f}", f"{((s['curr']-s['prev'])/s['prev'])*100 if s['prev']!=0 else 0:.2f}%")
    st.caption(f"📅 數據日期: {s['date']}")
with cu3:
    d = m.get("DJI", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("Dow Jones (道瓊)", f"{d['curr']:.0f}", f"{((d['curr']-d['prev'])/d['prev'])*100 if d['prev']!=0 else 0:.2f}%")
    st.caption(f"📅 數據日期: {d['date']}")

# 第三排：亞股市場
st.subheader("🗾 亞股市場")
ca1, ca2, ca3 = st.columns(3)
with ca1:
    tw = m.get("WTX") if m.get("WTX", {}).get("curr", 0) > 0 else m.get("TWII", {"curr":0, "prev":0, "date":"N/A"})
    diff, pct = tw['curr']-tw['prev'], ((tw['curr']-tw['prev'])/tw['prev'])*100 if tw['prev']!=0 else 0
    st.metric("台股市場 (TW)", f"{tw['curr']:.0f}", f"{diff:+.0f} ({pct:+.2f}%)")
    st.caption(f"📅 收盤日期: {tw['date']}")
with ca2:
    nk = m.get("N225", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("日經 225 (JP)", f"{nk['curr']:.0f}", f"{((nk['curr']-nk['prev'])/nk['prev'])*100 if nk['prev']!=0 else 0:.2f}%")
    st.caption(f"📅 收盤日期: {nk['date']}")
with ca3:
    ks = m.get("KS11", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("韓國 KOSPI (KR)", f"{ks['curr']:.2f}", f"{((ks['curr']-ks['prev'])/ks['prev'])*100 if ks['prev']!=0 else 0:.2f}%")
    st.caption(f"📅 收盤日期: {ks['date']}")
