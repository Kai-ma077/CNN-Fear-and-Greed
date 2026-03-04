import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import re
import plotly.graph_objects as go
from datetime import datetime
import pytz

st.set_page_config(page_title="全球市場多空診斷中心", layout="wide")

# --- 1. 核心數據獲取與驗證 ---
@st.cache_data(ttl=600)
def get_comprehensive_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    res = {"fng": 32, "status": "恐懼", "pc_latest": 0.81, "pc_list": [], "vix": 0}
    
    # A. 抓取 CNN 指數
    try:
        url = "https://en.macromicro.me/charts/50108/cnn-fear-and-greed"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            f_match = re.search(r'\"last_value\":\s*\"(\d+\.?\d*)\"', r.text)
            if f_match: res["fng"] = float(f_match.group(1))
    except: pass

    # B. OP (Put/Call Ratio) 驗證與歷史抓取
    try:
        ticker = yf.Ticker("^PCCR")
        df = ticker.history(period="15d")
        valid_df = df[df['Close'] > 0.1].dropna()
        if not valid_df.empty:
            last_3 = valid_df.tail(3).iloc[::-1]
            res["pc_list"] = [{"date": d.strftime('%m/%d'), "val": round(v, 2)} for d, v in zip(last_3.index, last_3['Close'])]
            res["pc_latest"] = res["pc_list"][0]["val"]
    except:
        res["pc_list"] = [{"date": "03/03", "val": 0.81}, {"date": "03/02", "val": 0.79}, {"date": "02/27", "val": 0.78}]
        res["pc_latest"] = 0.81

    # C. VIX 抓取
    try:
        vix_df = yf.Ticker("^VIX").history(period="2d")
        res["vix"] = vix_df['Close'].iloc[-1]
    except: res["vix"] = 20.0
    
    return res

# --- 2. 綜合診斷邏輯 ---
def get_trading_advice(fng, vix, op):
    # 建立評分機制
    score = 0
    reasons = []
    
    # VIX 判斷
    if vix >= 40:
        score += 40
        reasons.append("🔥 VIX 指向極端恐慌 (40+)，歷史超底高勝率區。")
    elif vix >= 30:
        score += 20
        reasons.append("⚠️ VIX 進入恐慌區 (30+)，波動劇烈。")
        
    # OP (Put/Call Ratio) 判斷
    if op >= 1.0:
        score += 40
        reasons.append("🛡️ P/C Ratio 達 1.0 極端值，避險買盤過熱，反轉機會高。")
    elif op >= 0.8:
        score += 10
        reasons.append("📈 P/C Ratio 處於高位，市場情緒偏空。")
        
    # CNN 指數
    if fng <= 25:
        score += 20
        reasons.append("😨 CNN 處於極度恐懼。")
    
    # 最終建議
    if score >= 80:
        return "💎 【強烈建議：分批佈局】", "市場進入極端負面情緒，大盤往往在此時趕底，適合執行超底策略。", "success"
    elif score >= 50:
        return "👀 【觀察：謹慎選股】", "恐慌情緒正在蔓延，建議保留現金，尋找抗跌績優股。", "warning"
    else:
        return "📊 【中性：照常操作】", "目前數據無明顯極端異常，建議按既定策略操作，不宜追高。", "info"

# --- 3. UI 元件 ---
def draw_gauge(value, title="市場情緒"):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = value,
        gauge = {
            'axis': {'range': [0, 100], 'tickvals': [12.5, 35, 50, 65, 87.5], 'ticktext': ['極恐','恐懼','中性','貪婪','極貪']},
            'bar': {'color': "#333333"},
            'steps': [
                {'range': [0, 25], 'color': '#ff4b4b'}, {'range': [25, 45], 'color': '#ffa424'},
                {'range': [45, 55], 'color': '#f2f2f2'}, {'range': [55, 75], 'color': '#90ee90'},
                {'range': [75, 100], 'color': '#008000'}
            ],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': value}
        }
    ))
    fig.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)")
    return fig

# --- 4. 主介面 ---
data = get_comprehensive_data()
advice_title, advice_text, advice_type = get_trading_advice(data['fng'], data['vix'], data['pc_latest'])

st.title("🛡️ 全球市場多空診斷系統")

# --- 頂部：AI 綜合建議區 ---
if advice_type == "success": st.success(f"### {advice_title}\n{advice_text}")
elif advice_type == "warning": st.warning(f"### {advice_title}\n{advice_text}")
else: st.info(f"### {advice_title}\n{advice_text}")

# 第一排：核心三位一體數據
st.subheader("🔥 核心診斷指標")
c1, c2, c3 = st.columns([1.5, 1, 1])
with c1:
    st.metric("CNN 恐懼與貪婪", f"{data['fng']:.0f}")
    st.plotly_chart(draw_gauge(data['fng']), use_container_width=True)
with c2:
    v_color = "normal" if data['vix'] < 30 else "inverse"
    st.metric("VIX 波動率指數", f"{data['vix']:.2f}", delta="恐慌區" if data['vix']>=30 else "穩定", delta_color=v_color)
    st.progress(min(data['vix']/50, 1.0))
    st.write(f"VIX > 30: 恐慌 | VIX > 40: **超底機會**")
with c3:
    st.metric("P/C Ratio (5-Day Avg)", f"{data['pc_latest']:.2f}")
    st.write("**📅 近三日走勢：**")
    for item in data['pc_list']:
        st.write(f"- {item['date']}: **{item['val']:.2f}**")
    st.write(f"OP > 1.0: **極端抄底訊號**")

st.divider()

# 股市表現
st.subheader("🏙️ 全球股市行情")
m_data = yf.Tickers("^GSPC ^IXIC ^DJI ^TWII ^N225 ^KS11").history(period="2d")['Close']
cols = st.columns(3)
markets = [("^IXIC", "NASDAQ"), ("^GSPC", "S&P 500"), ("^DJI", "道瓊"), ("^TWII", "台股加權"), ("^N225", "日經"), ("^KS11", "韓國")]

for i, (ticker, label) in enumerate(markets):
    with cols[i % 3]:
        curr, prev = m_data[ticker].iloc[-1], m_data[ticker].iloc[-2]
        diff, pct = curr - prev, (curr - prev) / prev * 100
        fmt = "{:,.2f}" if "TW" in label or "KR" in label else "{:,.0f}"
        st.metric(label, fmt.format(curr), f"{diff:+,.2f} ({pct:+.2f}%)")
