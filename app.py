import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="全球市場即時監控中心", layout="wide")

# --- 定義開盤時間備註函數 ---
def get_opening_remarks():
    now = datetime.now()
    weekday = now.weekday() # 0=Mon, 6=Sun
    
    # 亞股 (台日韓) 通常在週一至週五 08:00 - 09:00 開盤
    # 美股通常在週一至週五 22:30 開盤 (冬令時間)
    remarks = {}
    if weekday >= 5: # 週六或週日
        days_to_mon = 7 - weekday
        remarks['asia'] = f"📅 週末休市，下週一 {(now + timedelta(days=days_to_mon)).strftime('%m/%d')} 08:00-09:00 開盤"
        remarks['us'] = f"📅 週末休市，下週一 {(now + timedelta(days=days_to_mon)).strftime('%m/%d')} 22:30 開盤"
    else:
        remarks['asia'] = "🕒 亞股交易日：台(09:00)、日(08:00)、韓(08:00)"
        remarks['us'] = "🕒 美股交易日：22:30 開盤 (冬令時間)"
    return remarks

@st.cache_data(ttl=300)
def get_cnn_fng():
    url = "https://production.dataviz.cnn.io/index/feargreed/static/data"
    headers = {"User-Agent": "Mozilla/5.0", "Origin": "https://www.cnn.com", "Referer": "https://www.cnn.com/markets/fear-and-greed"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return {"val": data['market_rating_current']['score'], "text": data['market_rating_current']['rating'].upper(), "time": data['market_rating_current']['timestamp']}
    except: return None

@st.cache_data(ttl=300)
def get_market_data():
    tickers = {
        "VIX": "^VIX", "PCCR": "^PCCR", "NAS": "^IXIC", "SPX": "^GSPC", "DJI": "^DJI", "TWII": "^TWII", "N225": "^N225", "KS11": "^KS11"
    }
    results = {}
    for name, symbol in tickers.items():
        try:
            df = yf.Ticker(symbol).history(period="10d")
            if not df.empty:
                valid = df[df['Close'] > 0].dropna()
                curr = valid.iloc[-1]
                prev = valid.iloc[-2]
                results[name] = {
                    "curr": curr['Close'], "prev": prev['Close'], "date": valid.index[-1].strftime('%m/%d %H:%M')
                }
        except: results[name] = {"curr": 0, "prev": 0, "date": "N/A"}
    return results

# --- 介面開始 ---
st.title("🌎 全球多空情緒監控中心")
remarks = get_opening_remarks()
st.write(f"🕒 系統檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

fng = get_cnn_fng()
m_data = get_market_data()

# --- 第一排：核心情緒指標 ---
st.subheader("🔥 核心情緒指標")
c1, c2, c3 = st.columns(3)
with c1:
    if fng:
        st.metric("CNN 恐懼與貪婪", f"{fng['val']:.0f}", fng['text'])
        st.progress(int(fng['val']))
        st.caption(f"📅 數據時間: {fng['time'][:16]}")
with c2:
    v = m_data.get("VIX", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("VIX 恐慌指數", f"{v['curr']:.2f}", f"{v['curr']-v['prev']:.2f}", delta_color="inverse")
    st.caption(f"📅 數據時間: {v['date']}")
with c3:
    pc = m_data.get("PCCR", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("CBOE Put/Call Ratio", f"{pc['curr']:.2f}", f"{pc['curr']-pc['prev']:.2f}", delta_color="inverse")
    st.caption(f"📅 數據時間: {pc['date']} (昨值)")

st.divider()

# --- 第二排：美股市場 ---
st.subheader("🏙️ 美股市場")
st.info(remarks['us'])
cu1, cu2, cu3 = st.columns(3)
with cu1:
    nas = m_data.get("NAS", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("NASDAQ (小那)", f"{nas['curr']:.0f}", f"{((nas['curr']-nas['prev'])/nas['prev'])*100:.2f}%")
    st.caption(f"📅 數據時間: {nas['date']}")
with cu2:
    sp = m_data.get("SPX", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("S&P 500 (標普)", f"{sp['curr']:.0f}", f"{((sp['curr']-sp['prev'])/sp['prev'])*100:.2f}%")
    st.caption(f"📅 數據時間: {sp['date']}")
with cu3:
    dji = m_data.get("DJI", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("Dow Jones (道瓊)", f"{dji['curr']:.0f}", f"{((dji['curr']-dji['prev'])/dji['prev'])*100:.2f}%")
    st.caption(f"📅 數據時間: {dji['date']}")

# --- 第三排：亞股市場 ---
st.subheader("🗾 亞股市場")
st.info(remarks['asia'])
ca1, ca2, ca3 = st.columns(3)
with ca1:
    tw = m_data.get("TWII", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("台股加權 (TW)", f"{tw['curr']:.0f}", f"{tw['curr']-tw['prev']:.2f}")
    st.caption(f"📅 數據時間: {tw['date']}")
with ca2:
    nk = m_data.get("N225", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("日經 225 (JP)", f"{nk['curr']:.0f}", f"{((nk['curr']-nk['prev'])/nk['prev'])*100:.2f}%")
    st.caption(f"📅 數據時間: {nk['date']}")
with ca3:
    ks = m_data.get("KS11", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("韓國 KOSPI (KR)", f"{ks['curr']:.2f}", f"{((ks['curr']-ks['prev'])/ks['prev'])*100:.2f}%")
    st.caption(f"📅 數據時間: {ks['date']}")
