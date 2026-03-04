import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="全球市場情緒儀表板", layout="wide")

@st.cache_data(ttl=600)
def get_global_market():
    # 定義全球核心指數 Ticker
    tickers = {
        "VIX 恐慌指數": "^VIX",
        "Put/Call Ratio": "^PCCR",
        "標普 500 (US)": "^GSPC",
        "納斯達克 (US)": "^IXIC",
        "台指期貨 (TW)": "WTX=F", # 台灣期指連續合約
        "日經 225 (JP)": "^N225",
        "韓國綜合 (KR)": "^KS11"
    }
    
    results = {}
    for name, symbol in tickers.items():
        try:
            # 抓取 10 天數據確保能避開假日或延遲
            data = yf.Ticker(symbol).history(period="10d")
            if not data.empty:
                # 針對 PCCR 做特殊處理：如果最後一筆是 0，往前找非 0 的那一筆
                if name == "Put/Call Ratio":
                    valid_data = data[data['Close'] > 0]
                    curr = valid_data['Close'].iloc[-1] if not valid_data.empty else 0
                    prev = valid_data['Close'].iloc[-2] if len(valid_data) > 1 else 0
                else:
                    curr = data['Close'].iloc[-1]
                    prev = data['Close'].iloc[-2]
                
                results[name] = {"curr": curr, "prev": prev}
            else:
                results[name] = {"curr": 0, "prev": 0}
        except:
            results[name] = {"curr": 0, "prev": 0}
    return results

st.title("🌎 全球多空情緒監控中心")
st.write(f"最後更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (台北時間)")

data = get_global_market()

# --- 第一排：核心情緒指標 (VIX & PCCR) ---
st.subheader("🔥 核心情緒指標")
c1, c2 = st.columns(2)
with c1:
    v = data["VIX 恐慌指數"]
    st.metric("VIX 恐慌指數", f"{v['curr']:.2f}", f"{v['curr']-v['prev']:.2f}", delta_color="inverse")
with c2:
    pc = data["Put/Call Ratio"]
    st.metric("CBOE Put/Call Ratio (昨值)", f"{pc['curr']:.2f}", f"{pc['curr']-pc['prev']:.2f}", delta_color="inverse")
    st.caption("註：P/C Ratio 通常延遲一天更新")

st.divider()

# --- 第二排：美股與台股 ---
st.subheader("🏙️ 美股 & 台股")
c3, c4, c5 = st.columns(3)
with c3:
    sp = data["標普 500 (US)"]
    st.metric("S&P 500", f"{sp['curr']:.0f}", f"{((sp['curr']-sp['prev'])/sp['prev'])*100:.2f}%")
with c4:
    nas = data["納斯達克 (US)"]
    st.metric("NASDAQ", f"{nas['curr']:.0f}", f"{((nas['curr']-nas['prev'])/nas['prev'])*100:.2f}%")
with c5:
    tw = data["台指期貨 (TW)"]
    st.metric("台指期 (近月)", f"{tw['curr']:.0f}", f"{tw['curr']-tw['prev']:.0f}")

# --- 第三排：亞股市場 ---
st.subheader("🗾 亞股市場")
c6, c7 = st.columns(2)
with c6:
    nk = data["日經 225 (JP)"]
    st.metric("日經 225", f"{nk['curr']:.0f}", f"{((nk['curr']-nk['prev'])/nk['prev'])*100:.2f}%")
with c7:
    ks = data["韓國綜合 (KR)"]
    st.metric("韓國 KOSPI", f"{ks['curr']:.2f}", f"{((ks['curr']-ks['prev'])/ks['prev'])*100:.2f}%")

# --- 底部診斷 ---
st.divider()
if data["VIX 恐慌指數"]["curr"] > 25:
    st.error("🚨 警告：全球波動率攀升，避險情緒濃厚。")
elif data["VIX 恐慌指數"]["curr"] < 15:
    st.success("☀️ 提示：市場目前處於低波動穩定狀態。")
