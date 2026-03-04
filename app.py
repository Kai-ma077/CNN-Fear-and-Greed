import streamlit as st
import yfinance as yf
from fear_and_greed import pypi
import plotly.graph_objects as go
import pandas as pd

# 1. 網頁基本設定
st.set_page_config(page_title="市場情緒監控儀表板", layout="wide")

# 2. 定義數據抓取函數 (設定快取，避免頻繁抓取被封鎖)
@st.cache_data(ttl=600)
def get_market_data():
    # 抓取 VIX
    vix_data = yf.Ticker("^VIX").history(period="5d")
    current_vix = vix_data['Close'].iloc[-1]
    prev_vix = vix_data['Close'].iloc[-2]
    
    # 抓取 CNN 數據
    cnn_results = pypi.get()
    
    return current_vix, prev_vix, cnn_results

# 3. 標題與側邊欄
st.title("📊 市場情緒即時監控中心")
st.markdown("追蹤 VIX、CNN 恐懼與貪婪指數及期權比率")

try:
    vix, prev_vix, cnn = get_market_data()
    vix_delta = vix - prev_vix

    # 4. 頂部核心指標卡片
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("VIX 波動率指數", f"{vix:.2f}", f"{vix_delta:.2f} (vs 昨日)", delta_color="inverse")
        if vix > 30: st.error("⚠️ 市場極度恐慌")
        elif vix < 15: st.success("✅ 市場過度樂觀")

    with col2:
        st.metric("CNN 恐懼與貪婪指數", f"{cnn.value:.0f}", cnn.description)
        # 顯示簡易進度條當作指針
        st.progress(int(cnn.value))

    with col3:
        # 從 CNN 數據中提取 Put and Call Options 比率
        pc_data = next((item for item in cnn.extra_data if item['name'] == 'put_and_call_options'), None)
        if pc_ratio := pc_data.get('score'):
            st.metric("Put/Call Ratio (5D)", f"{pc_ratio:.2f}")
            if pc_ratio > 1.0: st.info("📈 看跌期權增加 (潛在反轉)")

    # 5. 詳細數據清單
    st.divider()
    with st.expander("查看所有 CNN 指標細節"):
        for item in cnn.extra_data:
            st.write(f"🔹 **{item['name']}**: {item['description']} (得分: {item['score']:.2f})")

    st.caption(f"數據最後更新時間: {cnn.last_update}")

except Exception as e:
    st.error(f"數據抓取失敗，請稍後重試。錯誤訊息: {e}")