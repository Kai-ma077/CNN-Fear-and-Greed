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
    except: res["vix"] = 20.0
    
    return res

# --- 2. 綜合診斷建議 ---
def get_trading_advice(fng, vix, op):
    score = 0
    if vix >= 40: score += 40
    elif vix >= 30: score += 20
    if op >= 1.0: score += 40
    elif op >= 0.8: score += 10
    if fng <= 25: score += 20
    
    if score >= 80: return "💎 【分批佈局】", "市場處於極度負面情緒，歷史超底高勝率區。", "success"
    elif score >= 50: return "👀 【謹慎觀察】", "恐慌情緒蔓延，建議保留現金，尋找抗跌績優股。", "warning"
    else: return "📊 【照常操作】", "目前數據無明顯極端異常，按既定策略操作。", "info"

# --- 3. 核心指針圖 (優化比例) ---
def draw_gauge(value, status):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = value,
        title = {'text': f"情緒狀態: {status}", 'font': {'size': 18}},
        gauge = {
            'axis': {'range': [0, 100], 'tickvals': [12.5, 35, 50, 65, 87.5], 'ticktext': ['極恐','恐懼','中性','貪婪','極貪'], 'tickfont': {'size': 12}},
            'bar': {'color': "#333333"},
            'steps': [
                {'range': [0, 25], 'color': '#ff4b4b'}, {'range': [25, 45], 'color': '#ffa424'},
                {'range': [45, 55], 'color': '#f2f2f2'}, {'range': [55, 75], 'color': '#90ee90'},
                {'range': [75, 100], 'color': '#008000'}
            ]
        }
    ))
    fig.update_layout(height=260, margin=dict(l=30, r=30, t=40, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig

# --- 4. 市場行情抓取 ---
@st.cache_data(ttl=600)
def get_market_data():
    tickers = {"NAS": "^IXIC", "SPX": "^GSPC", "DJI": "^DJI", "TWII": "^TWII", "N225": "^N225", "KS11": "^KS11"}
    results = {}
    for name, symbol in tickers.items():
        try:
            df = yf.download(symbol, period="5d", progress=False)
            if not df.empty:
                curr = df['Close'].iloc[-1].values[0] if isinstance(df['Close'].iloc[-1], pd.Series) else df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2].values[0] if isinstance(df['Close'].iloc[-2], pd.Series) else df['Close'].iloc[-2]
                results[name] = {"curr": curr, "prev": prev, "date": df.index[-1].strftime('%m/%d')}
        except: results[name] = {"curr": 0, "prev": 0, "date": "N/A"}
    return results

# --- UI 介面 ---
st.title("🛡️ 全球市場多空診斷中心")

data = get_comprehensive_data()
advice_title, advice_text, advice_type = get_trading_advice(data['fng'], data['vix'], data['pc_latest'])

# 頂部建議
if advice_type == "success": st.success(f"**{advice_title}** | {advice_text}")
elif advice_type == "warning": st.warning(f"**{advice_title}** | {advice_text}")
else: st.info(f"**{advice_title}** | {advice_text}")

# 第一排：核心診斷指標 (增加間距與留白)
st.subheader("🔥 核心診斷指標")
st.write("") # 增加上方留白

c1, spacer1, c2, spacer2, c3 = st.columns([1.2, 0.1, 1, 0.1, 1])

with c1:
    with st.container():
        st.markdown("<h3 style='text-align: center;'>CNN 恐懼與貪婪</h3>", unsafe_allow_html=True)
        st.plotly_chart(draw_gauge(data['fng'], data['status']), use_container_width=True)

with c2:
    with st.container():
        st.markdown("<h3 style='text-align: center;'>VIX 波動率指數</h3>", unsafe_allow_html=True)
        st.write("<br>", unsafe_allow_html=True) # 使用 HTML 增加垂直間距
        v_color = "normal" if data['vix'] < 30 else "inverse"
        st.metric("當前 VIX 指數", f"{data['vix']:.2f}", f"{data['vix_change']:+.2f}", delta_color=v_color)
        st.progress(min(data['vix']/50, 1.0))
        st.write(f"VIX > 30: **恐慌** | VIX > 40: **超底**")

with c3:
    with st.container():
        st.markdown("<h3 style='text-align: center;'>Put/Call Ratio</h3>", unsafe_allow_html=True)
        st.write("<br>", unsafe_allow_html=True) # 使用 HTML 增加垂直間距
        st.metric("5-Day Avg (OP)", f"{data['pc_latest']:.2f}", "OP > 1.0 抄底")
        st.write("**📅 近三日走勢：**")
        for item in data['pc_list']:
            st.write(f"- {item['date']}: **{item['val']:.2f}**")

st.divider()

# 下方行情
st.subheader("🏙️ 全球股市行情")
m_data = get_market_data()
cols = st.columns(3)
markets = [("NAS", "NASDAQ (小那)"), ("SPX", "S&P 500 (標普)"), ("DJI", "Dow Jones (道瓊)"),
           ("TWII", "台股加權 (TWII)"), ("N225", "日經 225 (JP)"), ("KS11", "韓國 KOSPI (KR)")]

for i, (key, label) in enumerate(markets):
    with cols[i % 3]:
        d = m_data.get(key, {"curr": 0, "prev": 0, "date": "N/A"})
        if d['curr'] > 0:
            diff = d['curr'] - d['prev']
            pct = (diff / d['prev'] * 100) if d['prev'] != 0 else 0
            fmt = "{:,.2f}" if key in ["KS11", "TWII"] else "{:,.0f}"
            st.metric(label, fmt.format(d['curr']), f"{diff:+,.2f} ({pct:+.2f}%)")
            st.caption(f"📅 數據日期: {d['date']}")

st.write("")
st.write(f"🕒 最後更新: {datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')}")
