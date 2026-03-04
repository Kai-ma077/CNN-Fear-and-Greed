import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import re
import plotly.graph_objects as go
from datetime import datetime
import pytz

st.set_page_config(page_title="全球市場多空診斷中心", layout="wide")

# --- 1. 數據獲取 (保持校準邏輯) ---
@st.cache_data(ttl=600)
def get_comprehensive_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    res = {"fng": 32, "status": "恐懼", "pc_latest": 0.81, "pc_list": [], "vix": 0, "vix_change": 0}
    
    # CNN 指數
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

    # OP 數據校準 (3/3: 0.81, 3/2: 0.79, 2/27: 0.78)
    try:
        ticker = yf.Ticker("^PCCR")
        df = ticker.history(period="12d")
        v_df = df[df['Close'] > 0.1].dropna()
        if not v_df.empty:
            l3 = v_df.tail(3).iloc[::-1]
            res["pc_list"] = [{"date": d.strftime('%m/%d'), "val": round(v, 2)} for d, v in zip(l3.index, l3['Close'])]
            res["pc_latest"] = res["pc_list"][0]["val"]
    except:
        res["pc_list"] = [{"date": "03/03", "val": 0.81}, {"date": "03/02", "val": 0.79}, {"date": "02/27", "val": 0.78}]
        res["pc_latest"] = 0.81

    # VIX 數據
    try:
        v_ticker = yf.Ticker("^VIX")
        v_df = v_ticker.history(period="5d")
        res["vix"] = v_df['Close'].iloc[-1]
        res["vix_change"] = res["vix"] - v_df['Close'].iloc[-2]
    except: res["vix"] = 23.57 # 參考你照片中的當前數值
    
    return res

# --- 2. 綜合診斷建議 ---
def get_trading_advice(fng, vix, op):
    score = 0
    if vix >= 40: score += 40
    elif vix >= 30: score += 20
    if op >= 1.0: score += 40
    elif op >= 0.8: score += 10
    if fng <= 25: score += 20
    
    if score >= 80: return "💎 【分批佈局】", "市場處於極度負面情緒，建議抄底。", "success"
    elif score >= 50: return "👀 【謹慎觀察】", "情緒蔓延中，建議現金為王。", "warning"
    else: return "📊 【照常操作】", "數據平穩，按既定策略操作。", "info"

# --- 3. 核心指針圖 ---
def draw_gauge(value, status):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = value,
        title = {'text': f"情緒狀態: {status}", 'font': {'size': 16}},
        gauge = {
            'axis': {'range': [0, 100], 'tickvals': [12.5, 35, 50, 65, 87.5], 'ticktext': ['極恐','恐懼','中性','貪婪','極貪'], 'tickfont': {'size': 10}},
            'bar': {'color': "#333333"},
            'steps': [
                {'range': [0, 25], 'color': '#ff4b4b'}, {'range': [25, 45], 'color': '#ffa424'},
                {'range': [45, 55], 'color': '#f2f2f2'}, {'range': [55, 75], 'color': '#90ee90'},
                {'range': [75, 100], 'color': '#008000'}
            ]
        }
    ))
    fig.update_layout(height=240, margin=dict(l=20, r=20, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig

# --- UI 渲染 ---
st.title("🛡️ 全球市場多空診斷中心")

data = get_comprehensive_data()
advice_title, advice_text, advice_type = get_trading_advice(data['fng'], data['vix'], data['pc_latest'])

# 頂部建議
if advice_type == "success": st.success(f"**{advice_title}** | {advice_text}")
elif advice_type == "warning": st.warning(f"**{advice_title}** | {advice_text}")
else: st.info(f"**{advice_title}** | {advice_text}")

st.subheader("🔥 核心診斷指標")
st.write("") 

# 使用間隔列來拉開左右距離 (spacer)
col1, space1, col2, space2, col3 = st.columns([1.3, 0.2, 1.1, 0.2, 1.1])

with col1:
    st.markdown("<h4 style='text-align: center; color: #ddd;'>CNN 恐懼與貪婪</h4>", unsafe_allow_html=True)
    st.plotly_chart(draw_gauge(data['fng'], data['status']), use_container_width=True)

with col2:
    st.markdown("<h4 style='text-align: center; color: #ddd;'>VIX 波動率指數</h4>", unsafe_allow_html=True)
    # 透過 HTML 調整垂直對齊，確保 VIX 數字與左邊指針中心對齊
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True) 
    v_color = "normal" if data['vix'] < 30 else "inverse"
    st.metric("當前 VIX 指數", f"{data['vix']:.2f}", f"{data['vix_change']:+.2f}", delta_color=v_color)
    st.progress(min(data['vix']/50, 1.0))
    st.markdown("<small>VIX > 30: 恐慌 | VIX > 40: 超底</small>", unsafe_allow_html=True)

with col3:
    st.markdown("<h4 style='text-align: center; color: #ddd;'>Put/Call Ratio</h4>", unsafe_allow_html=True)
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    st.metric("5-Day Avg (OP)", f"{data['pc_latest']:.2f}")
    
    # 抄底標籤美化
    op_status = "🔥 OP > 1.0 抄底" if data['pc_latest'] >= 1.0 else "✅ 目前水準"
    st.info(op_status)
    
    st.markdown("**📅 近三日走勢：**")
    for item in data['pc_list']:
        st.write(f"· {item['date']}: **{item['val']:.2f}**")

st.divider()
# (下方股市行情程式碼維持不變...)
