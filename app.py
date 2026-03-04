import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="全球市場情緒儀表板", layout="wide")

@st.cache_data(ttl=600)
def get_fng_index():
    # 這裡使用穩定性最高的公開 Fear & Greed API
    try:
        r = requests.get("https://api.alternative.me/fng/", timeout=10)
        if r.status_code == 200:
            data = r.json()['data'][0]
            return {"val": float(data['value']), "text": data['value_classification']}
    except:
        return {"val": 50, "text": "Neutral (Data Delay)"}

@st.cache_data(ttl=600)
def get_global_market():
    tickers = {
        "VIX 恐慌指數": "^VIX",
        "Put/Call Ratio": "^PCCR",
        "標普 500 (US)": "^GSPC",
        "納斯達克 (US)": "^IXIC",
        "台灣加權指數 (TW)": "^TWII",
        "日經 225 (JP)": "^N225",
        "韓國綜合 (KR)": "^KS11"
    }
    
    results = {}
    for name, symbol in tickers.items():
        try:
            data = yf.Ticker(symbol).history(period="20d")
            if not data.empty:
                valid_data = data[data['Close'] > 0].dropna()
                if not valid_data.empty:
                    curr = valid_data['Close'].iloc[-1]
                    prev = valid_data['Close'].iloc[-2] if len(valid_data) > 1 else curr
                    results[name] = {"curr": curr, "prev": prev}
            else:
                results[name] = {"curr": 0, "prev": 0}
        except:
            results[name] = {"curr": 0, "prev": 0}
    return results

st.title("🌎 全球多空情緒監控中心")
st.write(f"最後更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (台北時間)")

# 獲取數據
fng = get_fng_index()
data = get_global_market()

# --- 第一排：核心情緒指標 (加入恐懼與貪婪) ---
st.subheader("🔥 核心情緒指標")
c1, c2, c3 = st.columns(3)

with c1:
    # 顯示恐懼與貪婪指數
    st.metric("恐懼與貪婪指數", f"{fng['val']:.0f}", fng['text'])
    st.progress(int(fng['val']))

with c2:
    v = data["VIX 恐慌指數"]
    v_diff = v['curr'] - v['prev']
    st.metric("VIX 恐慌指數", f"{v['curr']:.2f}", f"{v_diff:.2f}", delta_color="inverse")
    
with c3:
    pc = data["Put/Call Ratio"]
    if pc['curr'] > 0:
        pc_diff = pc['curr'] - pc['prev']
        st.metric("CBOE Put/Call Ratio", f"{pc['curr']:.2f}", f"{pc_diff:.2f}", delta_color="inverse")
    else:
        st.metric("CBOE Put/Call Ratio", "結算中", "無昨值")

st.divider()

# --- 第二排：美股市場 ---
st.subheader("🏙️ 美股市場")
c_us1, c_us2 = st.columns(2)
with c_us1:
    sp = data["標普 500 (US)"]
    sp_pct = ((sp['curr']-sp['prev'])/sp['prev'])*100 if sp['prev'] != 0 else 0
    st.metric("S&P 500", f"{sp['curr']:.0f}", f"{sp_pct:.2f}%")
with c_us2:
    nas = data["納斯達克 (US)"]
    nas_pct = ((nas['curr']-nas['prev'])/nas['prev'])*100 if nas['prev'] != 0 else 0
    st.metric("NASDAQ", f"{nas['curr']:.0f}", f"{nas_pct:.2f}%")

# --- 第三排：亞股市場 (台股排第一) ---
st.subheader("🗾 亞股市場")
c_as1, c_as2, c_as3 = st.columns(3)
with c_as1:
    tw = data["台灣加權指數 (TW)"]
    tw_diff = tw['curr'] - tw['prev']
    st.metric("台股加權 (TW)", f"{tw['curr']:.0f}", f"{tw_diff:.2f}")
with c_as2:
    nk = data["日經 225 (JP)"]
    nk_pct = ((nk['curr']-nk['prev'])/nk['prev'])*100 if nk['prev'] != 0 else 0
    st.metric("日經 225 (JP)", f"{nk['curr']:.0f}", f"{nk_pct:.2f}%")
with c_as3:
    ks = data["韓國綜合 (KR)"]
    ks_pct = ((ks['curr']-ks['prev'])/ks['prev'])*100 if ks['prev'] != 0 else 0
    st.metric("韓國 KOSPI (KR)", f"{ks['curr']:.2f}", f"{ks_pct:.2f}%")

# --- 底部警示 ---
st.divider()
fng_val = fng['val']
if fng_val < 25:
    st.error(f"🚨 目前市場處於【極度恐懼】，歷史經驗通常是分批佈局的機會。")
elif fng_val > 75:
    st.warning(f"🚨 目前市場處於【極度貪婪】，請注意回撤風險。")
else:
    st.info(f"📊 市場目前情緒為 {fng['text']}，波動趨於穩定。")
