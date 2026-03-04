import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="市場情緒監控中心", layout="wide")

# 1. 強化版抓取函數：增加更多偽裝標頭
@st.cache_data(ttl=600)
def get_cnn_data():
    url = "https://production.dataviz.cnn.io/index/feargreed/static/data"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://www.cnn.com/markets/fear-and-greed",
        "Origin": "https://www.cnn.com"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            return f"Error: Status {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

@st.cache_data(ttl=600)
def get_vix_data():
    try:
        vix = yf.Ticker("^VIX").history(period="2d")
        return vix['Close'].iloc[-1], vix['Close'].iloc[-2]
    except:
        return 0.0, 0.0

st.title("📊 市場情緒即時監控中心")

# 執行抓取
cnn_res = get_cnn_data()
vix_curr, vix_prev = get_vix_data()

# --- 佈局：頂部指標 ---
col1, col2, col3 = st.columns(3)

with col1:
    vix_delta = vix_curr - vix_prev
    st.metric("VIX 波動率指數", f"{vix_curr:.2f}", f"{vix_delta:.2f}", delta_color="inverse")

with col2:
    # 判斷 CNN 數據是否成功抓取
    if isinstance(cnn_res, dict):
        # 嘗試目前已知的兩種 CNN API 結構
        fng_info = cnn_res.get('market_rating_current', cnn_res.get('fng', {}))
        score = fng_info.get('score', 0)
        rating = fng_info.get('rating', 'N/A').upper()
        
        st.metric("CNN 恐懼與貪婪", f"{score:.0f}", rating)
        st.progress(int(score) if 0 <= score <= 100 else 0)
    else:
        st.error(f"CNN 連線失敗: {cnn_res}")

with col3:
    if isinstance(cnn_res, dict) and 'indicator_data' in cnn_res:
        # 搜尋 Put/Call Ratio 指標
        pc_item = next((i for i in cnn_res['indicator_data'] if 'put_and_call' in i.get('instrument_id', '').lower() or 'put' in i.get('label', '').lower()), None)
        if pc_item:
            st.metric("Put/Call Ratio (5D)", f"{pc_item.get('score', 0):.2f}")
            st.caption(f"狀態: {pc_item.get('rating', 'N/A')}")
        else:
            st.write("找尋不到 P/C Ratio 數據")

# --- 詳細表格 ---
st.divider()
if isinstance(cnn_res, dict) and 'indicator_data' in cnn_res:
    st.subheader("CNN 七大子指標詳細數據")
    df = pd.DataFrame([
        {"指標名稱": i.get('label'), "目前得分": f"{i.get('score'):.2f}", "狀態": i.get('rating')}
        for i in cnn_res['indicator_data']
    ])
    st.table(df)
    
    ts = cnn_res.get('market_rating_current', {}).get('timestamp', str(datetime.now()))
    st.caption(f"數據最後更新: {ts}")

st.caption("數據來源：CNN Business & Yahoo Finance (每 10 分鐘自動快取)")
