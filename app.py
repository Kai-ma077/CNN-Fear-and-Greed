import streamlit as st
import yfinance as yf
import requests
import re
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="M平方 x VIX 監控中心", layout="wide")

@st.cache_data(ttl=3600) # M平方數據更新較慢，建議一小時更新一次即可
def get_macromicro_data():
    # 財經M平方的美股情緒指標頁面
    url = "https://www.macromicro.me/charts/47/s-p500-fear-greed-index"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.macromicro.me/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return f"Error: {response.status_code}"
        
        # 這裡使用正則表達式抓取 M平方頁面上的最新數值
        # 註：M平方常將數據放在 JavaScript 的變數中，我們直接挖取
        match = re.search(r'\"last_value\":\s*\"(\d+\.?\d*)\"', response.text)
        if match:
            return {"val": float(match.group(1)), "source": "MacroMicro"}
            
        # 備用方案：尋找特定標籤內的數值
        val_match = re.search(r'stat-value\">(\d+\.?\d*)', response.text)
        if val_match:
            return {"val": float(val_match.group(1)), "source": "MacroMicro"}

        return "數據格式解析失敗"
    except Exception as e:
        return str(e)

@st.cache_data(ttl=600)
def get_vix():
    vix = yf.Ticker("^VIX").history(period="2d")
    return vix['Close'].iloc[-1], vix['Close'].iloc[-2]

st.title("💹 財經M平方 x 全球情緒監控")

# 抓取數據
mm_data = get_macromicro_data()
vix_curr, vix_prev = get_vix()

col1, col2 = st.columns(2)

with col1:
    delta = vix_curr - vix_prev
    st.metric("VIX 波動率指數", f"{vix_curr:.2f}", f"{delta:.2f}", delta_color="inverse")
    st.write("數據源：Yahoo Finance")

with col2:
    if isinstance(mm_data, dict):
        score = mm_data['val']
        st.metric(f"M平方 恐懼與貪婪", f"{score:.2f}")
        st.progress(int(score) if 0 <= score <= 100 else 50)
        
        # 根據數值給予評價
        if score > 80: st.error("🔥 市場極度貪婪")
        elif score < 20: st.success("❄️ 市場極度恐慌")
        else: st.info("⚖️ 市場情緒中性")
    else:
        st.error(f"M平方 抓取失敗：{mm_data}")

st.divider()
st.subheader("💡 為什麼選財經M平方？")
st.write("1. **數據更全面**：M平方整合了更多散戶與大戶的綜合數據。")
st.write("2. **穩定性高**：相對於 CNN，M平方的網頁結構在亞洲訪問較穩定。")
st.write("3. **趨勢性強**：適合做中長期的情緒參考。")

st.caption(f"系統檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
