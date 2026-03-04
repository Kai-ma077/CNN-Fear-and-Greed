import streamlit as st
import yfinance as yf
import requests
import re
import json
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="市場情緒監控中心", layout="wide")

@st.cache_data(ttl=600)
def get_cnn_data_via_scraping():
    url = "https://www.cnn.com/markets/fear-and-greed"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return f"Error: HTTP {response.status_code}"
        
        # 使用正規表達式從 HTML 中挖出隱藏的 JSON 數據
        # CNN 的數據通常埋在一個 <script> 標籤裡的 JavaScript 物件中
        pattern = r'\"fear_and_greed\":({.*?})'
        match = re.search(pattern, response.text)
        
        if match:
            data_str = match.group(1)
            # 補齊括號並解析
            return json.loads(data_str)
        
        # 備用方案：如果 JSON 埋藏位置變了，尋找另一種標籤
        pattern_alt = r'fearAndGreed\":({.*?})'
        match_alt = re.search(pattern_alt, response.text)
        if match_alt:
            return json.loads(match_alt.group(1))
            
        return "無法在網頁中定位數據標籤"
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

# 執行抓取
cnn_res = get_cnn_data_via_scraping()
vix_curr, vix_prev = get_vix_data()

# --- 第一排：核心數據 ---
col1, col2, col3 = st.columns(3)

with col1:
    vix_delta = vix_curr - vix_prev
    st.metric("VIX 波動率指數", f"{vix_curr:.2f}", f"{vix_delta:.2f}", delta_color="inverse")

with col2:
    if isinstance(cnn_res, dict):
        score = cnn_res.get('score', 0)
        rating = cnn_res.get('rating', 'UNKNOWN').upper()
        st.metric("CNN 恐懼與貪婪", f"{score:.0f}", rating)
        st.progress(int(score) if 0 <= score <= 100 else 0)
    else:
        st.error(f"CNN 抓取失敗：{cnn_res}")
        st.info("提示：嘗試直接訪問官網確認是否正常。")

with col3:
    if isinstance(cnn_res, dict):
        # 嘗試從 cnn_res 中找尋指標數據
        # HTML 爬取後的結構可能較扁平
        st.write("📈 系統連線成功")
        st.caption("詳細子指標請見下方表格")

# --- 第二排：詳細表格 ---
st.divider()
if isinstance(cnn_res, dict):
    st.subheader("CNN 指標歷史趨勢 (得分)")
    # 這裡顯示目前抓到的主要分數與狀態
    st.write(f"當前得分：**{cnn_res.get('score', 'N/A')}**")
    st.write(f"當前評級：**{cnn_res.get('rating', 'N/A')}**")
    st.write(f"昨日得分：**{cnn_res.get('previous_close', 'N/A')}**")

st.caption(f"最後更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
