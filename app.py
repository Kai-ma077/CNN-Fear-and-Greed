import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="專業情緒監控中心", layout="wide")

@st.cache_data(ttl=600)
def get_financial_data():
    # 抓取三個核心指標：VIX, Put/Call Ratio 指數, 標普500
    tickers = {
        "VIX": "^VIX",
        "Put/Call Ratio": "^PCCR",  # CBOE Put/Call Ratio 指數
        "S&P 500": "^GSPC"
    }
    
    results = {}
    for name, symbol in tickers.items():
        try:
            data = yf.Ticker(symbol).history(period="5d")
            if not data.empty:
                curr = data['Close'].iloc[-1]
                prev = data['Close'].iloc[-2]
                results[name] = {"curr": curr, "prev": prev}
            else:
                results[name] = {"curr": 0, "prev": 0}
        except:
            results[name] = {"curr": 0, "prev": 0}
    return results

st.title("🏛️ 專業市場情緒監控中心 (API 穩定版)")
st.write("本系統直接對接 Yahoo Finance API，確保 24 小時不中斷連線。")

# 獲取數據
data = get_financial_data()

# --- 第一排：核心指標卡片 ---
col1, col2, col3 = st.columns(3)

with col1:
    v = data["VIX"]
    delta = v["curr"] - v["prev"]
    st.metric("VIX 恐慌指數", f"{v['curr']:.2f}", f"{delta:.2f}", delta_color="inverse")
    if v["curr"] > 25: st.warning("⚠️ 市場波動劇烈")

with col2:
    pc = data["Put/Call Ratio"]
    pc_delta = pc["curr"] - pc["prev"]
    # PCCR 通常在 0.6~1.2 之間波動
    st.metric("CBOE Put/Call Ratio", f"{pc['curr']:.2f}", f"{pc_delta:.2f}", delta_color="inverse")
    if pc["curr"] > 1.0: st.info("📈 看跌期權增加，暗示市場恐懼")

with col3:
    sp = data["S&P 500"]
    sp_delta = ((sp["curr"] - sp["prev"]) / sp["prev"]) * 100
    st.metric("S&P 500 指數", f"{sp['curr']:.0f}", f"{sp_delta:.2f}%")

# --- 第二排：自定義情緒判斷 ---
st.divider()
st.subheader("🤖 AI 情緒診斷")

# 簡單的邏輯判斷
vix_val = data["VIX"]["curr"]
pc_val = data["Put/Call Ratio"]["curr"]

if vix_val > 25 and pc_val > 1.0:
    st.error("### 當前市場狀態：極度恐慌 (Extreme Fear)")
    st.write("VIX 與 Put/Call Ratio 同步走高，市場情緒低迷，通常是潛在的買入觀察點。")
elif vix_val < 15 and pc_val < 0.7:
    st.success("### 當前市場狀態：過度樂觀 (Extreme Greed)")
    st.write("市場非常放鬆，追高風險正在增加，請注意回撤風險。")
else:
    st.info("### 當前市場狀態：中性盤整 (Neutral)")
    st.write("指標處於正常區間，建議觀察標普 500 支撐位。")

st.caption(f"最後更新時間 (UTC): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
