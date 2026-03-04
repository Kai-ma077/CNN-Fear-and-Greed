import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="市場情緒監控中心", layout="wide")

@st.cache_data(ttl=600)
def get_cnn_data():
    # 這是 2026 年 CNN 最新的數據接口路徑
    url = "https://production.dataviz.cnn.io/index/feargreed/static/data"
    
    # 強化偽裝：類比真實瀏覽器的所有請求特徵
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://www.cnn.com/markets/fear-and-greed",
        "Origin": "https://www.cnn.com",
        "Cache-Control": "no-cache"
    }
    
    try:
        # 嘗試主要路徑
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
        
        # 如果主要路徑失敗 (404)，嘗試備用路徑 (CNN 有時會切換到這個)
        backup_url = "https://www.cnn.com/markets/fear-and-greed/api/data"
        response = requests.get(backup_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
            
        return f"Status {response.status_code}"
    except Exception as e:
        return str(e)

@st.cache_data(ttl=600)
def get_vix_data():
    try:
        vix = yf.Ticker("^VIX").history(period="2d")
        return vix['Close'].iloc[-1], vix['Close'].iloc[-2]
    except:
        return 0.0, 0.0

st.title("📊 市場情緒即時監控中心")

cnn_res = get_cnn_data()
vix_curr, vix_prev = get_vix_data()

# --- 第一排：核心數據 ---
col1, col2, col3 = st.columns(3)

with col1:
    vix_delta = vix_curr - vix_prev
    st.metric("VIX 波動率指數", f"{vix_curr:.2f}", f"{vix_delta:.2f}", delta_color="inverse")

with col2:
    if isinstance(cnn_res, dict):
        # 2026 年新結構通常在 'fng' 或 'market_rating' 下
        fng_data = cnn_res.get('fng', cnn_res.get('market_rating_current', {}))
        score = fng_data.get('score', 0)
        rating = fng_data.get('rating', 'UNKNOWN').upper()
        
        st.metric("CNN 恐懼與貪婪", f"{score:.0f}", rating)
        st.progress(int(score) if 0 <= score <= 100 else 0)
    else:
        st.error(f"CNN 數據抓取失敗：{cnn_res}")
        st.info("提示：CNN 可能暫時封鎖了雲端伺服器的 IP。")

with col3:
    if isinstance(cnn_res, dict) and 'indicator_data' in cnn_res:
        # 廣泛搜尋 Put/Call Ratio 指標
        pc = next((i for i in cnn_res['indicator_data'] if 'put' in i.get('label', '').lower() or 'put' in i.get('instrument_id', '').lower()), None)
        if pc:
            st.metric("Put/Call Ratio (5D)", f"{pc.get('score', 0):.2f}")
            st.caption(f"當前狀態: {pc.get('rating', 'N/A')}")
        else:
            st.write("目前無法取得期權數據")

# --- 第二排：詳細指標表格 ---
st.divider()
if isinstance(cnn_res, dict) and 'indicator_data' in cnn_res:
    st.subheader("CNN 七大子指標詳細清單")
    table_data = []
    for i in cnn_res['indicator_data']:
        table_data.append({
            "指標": i.get('label', '未知'),
            "得分": f"{i.get('score', 0):.2f}",
            "狀態": i.get('rating', 'N/A')
        })
    st.table(pd.DataFrame(table_data))

st.caption(f"最後檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
