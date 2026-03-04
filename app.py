import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime

# 1. 網頁基本設定
st.set_page_config(page_title="市場情緒監控中心", layout="wide")

# 2. 定義抓取 CNN 數據的函數 (更新 API 路徑與邏輯)
@st.cache_data(ttl=600)
def get_cnn_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.cnn.com/markets/fear-and-greed'
    }
    # 這是 CNN 目前最穩定的資料接口
    url = "https://production.dataviz.cnn.io/index/feargreed/static/data"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None

# 3. 定義抓取 VIX 數據
@st.cache_data(ttl=600)
def get_vix_data():
    try:
        vix = yf.Ticker("^VIX").history(period="2d")
        return vix['Close'].iloc[-1], vix['Close'].iloc[-2]
    except:
        return 0.0, 0.0

st.title("📊 市場情緒即時監控中心")

# 執行數據抓取
cnn_json = get_cnn_data()
vix_curr, vix_prev = get_vix_data()

# --- 佈局：頂部核心指標 ---
col1, col2, col3 = st.columns(3)

with col1:
    vix_delta = vix_curr - vix_prev
    st.metric("VIX 波動率指數", f"{vix_curr:.2f}", f"{vix_delta:.2f}", delta_color="inverse")
    if vix_curr > 25: st.warning("市場波動加劇")

with col2:
    if cnn_json and 'fng' in cnn_json:
        # 嘗試從新的結構中抓取
        fng_val = cnn_json.get('fng', {}).get('score', 0)
        fng_text = cnn_json.get('fng', {}).get('rating', 'N/A').upper()
        st.metric("CNN 恐懼與貪婪", f"{fng_val:.0f}", fng_text)
        st.progress(int(fng_val))
    else:
        # 如果結構變了，嘗試舊路徑或顯示錯誤
        try:
            fng_val = cnn_json['market_rating_current']['score']
            st.metric("CNN 恐懼與貪婪", f"{fng_val:.0f}", "更新中")
            st.progress(int(fng_val))
        except:
            st.error("CNN 數據格式變更中")

with col3:
    if cnn_json and 'indicator_data' in cnn_json:
        # 尋找 Put/Call Ratio
        pc_item = next((i for i in cnn_json['indicator_data'] if 'put_and_call_options' in str(i.get('instrument_id', '')) or 'Put and Call Options' in str(i.get('label', ''))), None)
        if pc_item:
            st.metric("Put/Call Ratio (5D)", f"{pc_item['score']:.2f}")
            if pc_item['score'] > 1.0: st.info("看跌期權佔優")
        else:
            st.write("尋找 Put/Call Ratio 中...")

# --- 佈局：詳細清單 ---
st.divider()
if cnn_json and 'indicator_data' in cnn_json:
    st.subheader("CNN 七大子指標詳細數據")
    df_list = []
    for item in cnn_json['indicator_data']:
        df_list.append({
            "指標": item.get('label', '未知'),
            "得分": f"{item.get('score', 0):.2f}",
            "狀態": item.get('rating', 'N/A')
        })
    st.table(pd.DataFrame(df_list))
    
    # 顯示最後更新時間
    ts = cnn_json.get('fng', {}).get('timestamp', str(datetime.now()))
    st.caption(f"數據最後更新: {ts}")
else:
    st.info("正在嘗試連接 CNN 伺服器，請確保網路正常。")

st.caption("數據來源：CNN Business & Yahoo Finance (每 10 分鐘自動快取)")
