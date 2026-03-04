import streamlit as st
import yfinance as yf
import requests
import pandas as pd

# 1. 網頁基本設定
st.set_page_config(page_title="市場情緒監控中心", layout="wide")

# 2. 定義抓取 CNN 數據的函數
@st.cache_data(ttl=600)
def get_cnn_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    url = "https://production.dataviz.cnn.io/index/feargreed/static/data"
    r = requests.get(url, headers=headers)
    return r.json()

# 3. 定義抓取 VIX 數據
@st.cache_data(ttl=600)
def get_vix_data():
    vix = yf.Ticker("^VIX").history(period="2d")
    return vix['Close'].iloc[-1], vix['Close'].iloc[-2]

st.title("📊 市場情緒即時監控中心")

# --- 開始邏輯處理 ---
try:
    # 執行數據抓取
    cnn_data = get_cnn_data()
    vix_curr, vix_prev = get_vix_data()
    
    # 頂部三大指標佈局
    col1, col2, col3 = st.columns(3)
    
    with col1:
        vix_delta = vix_curr - vix_prev
        st.metric("VIX 波動率指數", f"{vix_curr:.2f}", f"{vix_delta:.2f}", delta_color="inverse")
    
    with col2:
        fng_val = cnn_data['market_rating_current']['score']
        fng_text = cnn_data['market_rating_current']['rating'].upper()
        st.metric("CNN 恐懼與貪婪", f"{fng_val:.0f}", fng_text)
        st.progress(int(fng_val))
        
    with col3:
        # 尋找 Put/Call Ratio 指標 (在 indicator_data 列表中尋找正確的標籤)
        pc_item = next((i for i in cnn_data['indicator_data'] if 'put_and_call_options' in i['instrument_id']), None)
        if pc_item:
            st.metric("Put/Call Ratio (5D)", f"{pc_item['score']:.2f}")
        else:
            st.write("暫無 Put/Call Ratio 數據")

    # 下方詳細數據表格
    st.divider()
    st.subheader("各項子指標細節")
    
    indicators = []
    for item in cnn_data['indicator_data']:
        indicators.append({
            "指標名稱": item['label'],
            "目前得分": f"{item['score']:.2f}",
            "狀態": item.get('rating', 'N/A')
        })
    st.table(pd.DataFrame(indicators))
    st.caption(f"數據最後更新時間: {cnn_data['market_rating_current']['timestamp']}")

except Exception as e:
    st.error(f"發生錯誤：{e}")
    st.info("提示：這可能是因為 CNN 接口暫時變動或連線不穩。")

st.caption("數據來源：CNN Business & Yahoo Finance")
