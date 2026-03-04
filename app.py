import streamlit as st
import yfinance as yf
import requests
import re
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="市場情緒監控中心", layout="wide")

@st.cache_data(ttl=600)
def fetch_cnn_sentiment():
    # 嘗試三個可能的數據源
    urls = [
        "https://production.dataviz.cnn.io/index/feargreed/static/data",
        "https://www.cnn.com/markets/fear-and-greed",
        "https://api.alternative.me/fng/" # 備用方案：加密貨幣恐懼貪婪(如果CNN完全斷線時的參考)
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    # 策略 1: 嘗試直接抓取 API
    try:
        r = requests.get(urls[0], headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            # 兼容多種 JSON 結構
            fng = data.get('fng', data.get('market_rating_current', {}))
            return {"score": fng.get('score'), "rating": fng.get('rating'), "source": "CNN API"}
    except:
        pass

    # 策略 2: 暴力搜尋網頁中的數字 (Regex 強化)
    try:
        r = requests.get(urls[1], headers=headers, timeout=10)
        # 尋找像是 "score":65.123 或 "rating":"greed" 的字眼
        score_match = re.search(r'\"score\":(\d+\.?\d*)', r.text)
        rating_match = re.search(r'\"rating\":\"(\w+)\"', r.text)
        
        if score_match:
            return {
                "score": float(score_match.group(1)),
                "rating": rating_match.group(1) if rating_match else "Unknown",
                "source": "CNN Page Scraping"
            }
    except:
        pass

    return None

@st.cache_data(ttl=600)
def get_vix():
    vix = yf.Ticker("^VIX").history(period="2d")
    return vix['Close'].iloc[-1], vix['Close'].iloc[-2]

st.title("📊 市場情緒即時監控中心")

# 獲取數據
cnn_data = fetch_cnn_sentiment()
vix_curr, vix_prev = get_vix()

col1, col2 = st.columns(2)

with col1:
    delta = vix_curr - vix_prev
    st.metric("VIX 波動率指數", f"{vix_curr:.2f}", f"{delta:.2f}", delta_color="inverse")

with col2:
    if cnn_data:
        st.metric(f"CNN 恐懼與貪婪 ({cnn_data['source']})", 
                  f"{cnn_data['score']:.0f}", 
                  cnn_data['rating'].upper())
        st.progress(int(cnn_data['score']))
    else:
        st.error("CNN 數據目前無法獲取")
        st.info("由於 CNN 加強了爬蟲防護，Streamlit 雲端伺服器可能被暫時封鎖 IP。")

st.divider()
st.write("### 💡 為什麼 CNN 數據抓不到？")
st.write("1. **IP 封鎖：** CNN 偵測到請求來自數據中心（AWS/GCP），這通常會被直接拒絕。")
st.write("2. **動態渲染：** 數據可能透過瀏覽器端 JavaScript 生成，傳統爬蟲抓不到。")

st.caption(f"檢查時間: {datetime.now().strftime('%H:%M:%S')}")
