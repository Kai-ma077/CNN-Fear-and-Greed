import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="全球市場情緒監控中心", layout="wide")

# --- 定義開盤時間與時區處理 ---
def get_opening_remarks():
    now = datetime.now(pytz.timezone('Asia/Taipei'))
    weekday = now.weekday()
    remarks = {}
    if weekday >= 5:
        days_to_mon = 7 - weekday
        remarks['asia'] = f"📅 週末休市，下週一 {(now + timedelta(days=days_to_mon)).strftime('%m/%d')} 09:00 開盤"
        remarks['us'] = f"📅 週末休市，下週一 {(now + timedelta(days=days_to_mon)).strftime('%m/%d')} 22:30 開盤"
    else:
        remarks['asia'] = "🕒 亞股交易日：台(13:45期貨收)、日(14:00收)、韓(14:30收)"
        remarks['us'] = "🕒 美股交易日：22:30 開盤 (冬令時間)"
    return remarks

@st.cache_data(ttl=300)
def get_cnn_fng():
    url = "https://production.dataviz.cnn.io/index/feargreed/static/data"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return {"val": data['market_rating_current']['score'], "text": data['market_rating_current']['rating'].upper(), "time": data['market_rating_current']['timestamp']}
    except: return None

@st.cache_data(ttl=300)
def get_market_data():
    # WTX=F 為台指期連續合約
    tickers = {
        "VIX": "^VIX", "PCCR": "^PCCR", "NAS": "^IXIC", "SPX": "^GSPC", "DJI": "^DJI", 
        "WTX": "WTX=F", "N225": "^N225", "KS11": "^KS11"
    }
    results = {}
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            # 抓取日線數據算漲跌
            df_daily = ticker.history(period="5d")
            if not df_daily.empty:
                valid_daily = df_daily[df_daily['Close'] > 0].dropna()
                curr_price = valid_daily['Close'].iloc[-1]
                prev_price = valid_daily['Close'].iloc[-2]
                
                # 抓取分鐘線取得精確成交時間
                df_min = ticker.history(period="1d", interval="1m")
                if not df_min.empty:
                    last_time = df_min.index[-1].astimezone(pytz.timezone('Asia/Taipei'))
                    time_str = last_time.strftime('%m/%d %H:%M')
                else:
                    # 盤後/休市期間的手動時間標註
                    last_date = valid_daily.index[-1].strftime('%m/%d')
                    if name == "WTX": time_str = f"{last_date} 13:45"
                    elif name == "N225": time_str = f"{last_date} 14:00"
                    elif name == "KS11": time_str = f"{last_date} 14:30"
                    else: time_str = f"{last_date} 收盤"
                
                results[name] = {"curr": curr_price, "prev": prev_price, "date": time_str}
        except:
            results[name] = {"curr": 0, "prev": 0, "date": "N/A"}
    return results

# --- UI 渲染 ---
st.title("🌎 全球多空情緒監控中心")
remarks = get_opening_remarks()
fng = get_cnn_fng()
m_data = get_market_data()

# 核心指標
st.subheader("🔥 核心情緒指標")
c1, c2, c3 = st.columns(3)
with c1:
    if fng:
        st.metric("CNN 恐懼與貪婪", f"{fng['val']:.0f}", fng['text'])
        st.progress(int(fng['val']))
        st.caption(f"📅 數據時間: {fng['time'][:16].replace('T', ' ')}")
with c2:
    v = m_data.get("VIX", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("VIX 恐慌指數", f"{v['curr']:.2f}", f"{v['curr']-v['prev']:.2f}", delta_color="inverse")
    st.caption(f"📅 最後成交: {v['date']}")
with c3:
    pc = m_data.get("PCCR", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("CBOE Put/Call Ratio", f"{pc['curr']:.2f}", f"{pc['curr']-pc['prev']:.2f}", delta_color="inverse")
    st.caption(f"📅 數據時間: {pc['date']}")

st.divider()

# 美股市場
st.subheader("🏙️ 美股市場")
st.info(remarks['us'])
cu1, cu2, cu3 = st.columns(3)
with cu1:
    nas = m_data.get("NAS", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("NASDAQ (小那)", f"{nas['curr']:.0f}", f"{((nas['curr']-nas['prev'])/nas['prev'])*100:.2f}%")
    st.caption(f"📅 最後成交: {nas['date']}")
with cu2:
    sp = m_data.get("SPX", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("S&P 500 (標普)", f"{sp['curr']:.0f}", f"{((sp['curr']-sp['prev'])/sp['prev'])*100:.2f}%")
    st.caption(f"📅 最後成交: {sp['date']}")
with cu3:
    dji = m_data.get("DJI", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("Dow Jones (道瓊)", f"{dji['curr']:.0f}", f"{((dji['curr']-dji['prev'])/dji['prev'])*100:.2f}%")
    st.caption(f"📅 最後成交: {dji['date']}")

# 亞股市場
st.subheader("🗾 亞股市場")
st.info(remarks['asia'])
ca1, ca2, ca3 = st.columns(3)
with ca1:
    tw = m_data.get("WTX", {"curr":0, "prev":0, "date":"N/A"})
    tw_diff = tw['curr'] - tw['prev']
    tw_pct = (tw_diff / tw['prev']) * 100 if tw['prev'] != 0 else 0
    # 這裡會同時顯示點數與百分比
    st.metric("台指期貨 (WTX)", f"{tw['curr']:.0f}", f"{tw_diff:+.0f} ({tw_pct:+.2f}%)")
    st.caption(f"📅 最後成交: {tw['date']}")
with ca2:
    nk = m_data.get("N225", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("日經 225 (JP)", f"{nk['curr']:.0f}", f"{((nk['curr']-nk['prev'])/nk['prev'])*100:.2f}%")
    st.caption(f"📅 收盤時間: {nk['date']}")
with ca3:
    ks = m_data.get("KS11", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("韓國 KOSPI (KR)", f"{ks['curr']:.2f}", f"{((ks['curr']-ks['prev'])/ks['prev'])*100:.2f}%")
    st.caption(f"📅 收盤時間: {ks['date']}")
