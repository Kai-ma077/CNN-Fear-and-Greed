import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="全球市場情緒儀表板", layout="wide")

@st.cache_data(ttl=600)
def get_global_market():
    # 更新後的 Ticker 清單
    tickers = {
        "VIX 恐慌指數": "^VIX",
        "Put/Call Ratio": "^PCCR",
        "標普 500 (US)": "^GSPC",
        "納斯達克 (US)": "^IXIC",
        "台灣加權指數 (TW)": "^TWII", # 使用大盤指數最穩定
        "日經 225 (JP)": "^N225",
        "韓國綜合 (KR)": "^KS11"
    }
    
    results = {}
    for name, symbol in tickers.items():
        try:
            # 抓取 20 天數據，確保能跨越長假與結算延遲
            data = yf.Ticker(symbol).history(period="20d")
            if not data.empty:
                # 核心修正：P/C Ratio 若當日為 0 或 NaN，自動尋找最近一筆有效值
                valid_data = data[data['Close'] > 0].dropna()
                if not valid_data.empty:
                    curr = valid_data['Close'].iloc[-1]
                    prev = valid_data['Close'].iloc[-2] if len(valid_data) > 1 else curr
                else:
                    curr, prev = 0, 0
                
                results[name] = {"curr": curr, "prev": prev}
            else:
                results[name] = {"curr": 0, "prev": 0}
        except:
            results[name] = {"curr": 0, "prev": 0}
    return results

st.title("🌎 全球多空情緒監控中心")
st.write(f"最後更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (台北時間)")

data = get_global_market()

# --- 第一排：核心情緒指標 ---
st.subheader("🔥 核心情緒指標")
c1, c2 = st.columns(2)
with c1:
    v = data["VIX 恐慌指數"]
    v_diff = v['curr'] - v['prev']
    st.metric("VIX 恐慌指數", f"{v['curr']:.2f}", f"{v_diff:.2f}", delta_color="inverse")
    
with c2:
    pc = data["Put/Call Ratio"]
    # 如果抓不到 PCCR，提示用戶可能處於交易所結算時段
    if pc['curr'] > 0:
        pc_diff = pc['curr'] - pc['prev']
        st.metric("CBOE Put/Call Ratio (昨值)", f"{pc['curr']:.2f}", f"{pc_diff:.2f}", delta_color="inverse")
    else:
        st.metric("CBOE Put/Call Ratio", "數據更新中", "請稍後再試")
    st.caption("註：Put/Call Ratio 數據通常在美股盤後 4-6 小時才會產出昨值")

st.divider()

# --- 第二排：美股市場 ---
st.subheader("🏙️ 美股市場")
c3, c4 = st.columns(2)
with c3:
    sp = data["標普 500 (US)"]
    sp_pct = ((sp['curr']-sp['prev'])/sp['prev'])*100 if sp['prev'] != 0 else 0
    st.metric("S&P 500", f"{sp['curr']:.0f}", f"{sp_pct:.2f}%")
with c4:
    nas = data["納斯達克 (US)"]
    nas_pct = ((nas['curr']-nas['prev'])/nas['prev'])*100 if nas['prev'] != 0 else 0
    st.metric("NASDAQ", f"{nas['curr']:.0f}", f"{nas_pct:.2f}%")

# --- 第三排：亞股市場 (台股排第一) ---
st.subheader("🗾 亞股市場")
c5, c6, c7 = st.columns(3)
with c5:
    tw = data["台灣加權指數 (TW)"]
    tw_diff = tw['curr'] - tw['prev']
    st.metric("台股加權 (TW)", f"{tw['curr']:.0f}", f"{tw_diff:.2f}")
with c6:
    nk = data["日經 225 (JP)"]
    nk_pct = ((nk['curr']-nk['prev'])/nk['prev'])*100 if nk['prev'] != 0 else 0
    st.metric("日經 225 (JP)", f"{nk['curr']:.0f}", f"{nk_pct:.2f}%")
with c7:
    ks = data["韓國綜合 (KR)"]
    ks_pct = ((ks['curr']-ks['prev'])/ks['prev'])*100 if ks['prev'] != 0 else 0
    st.metric("韓國 KOSPI (KR)", f"{ks['curr']:.2f}", f"{ks_pct:.2f}%")

# --- 底部警示 ---
st.divider()
vix_val = data["VIX 恐慌指數"]["curr"]
if vix_val > 25:
    st.error(f"⚠️ 當前 VIX 為 {vix_val:.2f}，市場情緒恐慌，請注意風險控管。")
elif vix_val < 15:
    st.success(f"☀️ 當前 VIX 為 {vix_val:.2f}，市場處於穩定區間。")
else:
    st.info("📊 市場情緒目前處於中性水平。")
