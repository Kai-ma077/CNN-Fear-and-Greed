import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import re
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="全球市場情緒監控中心", layout="wide")

# --- 1. 定義數據抓取邏輯 (玩股網 Fear & Greed) ---
@st.cache_data(ttl=600)
def get_wantgoo_fng():
    url = "https://www.wantgoo.com/global/macroeconomics/fearandgreed"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.wantgoo.com/"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            # 使用正則表達式尋找頁面中的當日數值
            # 玩股網通常會將當日數值放在 "今日 32" 或特定的 JSON 結構中
            score_match = re.search(r'當日.*?(\d+)', r.text)
            rating_match = re.search(r'當日.*?([\u4e00-\u9fa5]{2})', r.text) # 抓取中文狀態如：恐懼
            
            # 若正則失敗，嘗試尋找 Highcharts 數據中的最新值
            if not score_match:
                score_match = re.search(r'\"y\":(\d+)', r.text)
            
            score = int(score_match.group(1)) if score_match else 50
            rating = rating_match.group(1) if rating_match else "數據獲取中"
            
            return {"val": score, "text": rating}
        return {"val": 0, "text": "連線失敗"}
    except:
        return {"val": 0, "text": "解析錯誤"}

@st.cache_data(ttl=600)
def get_market_data():
    tickers = {
        "VIX": "^VIX", "PCCR": "^PCCR", "NAS": "^IXIC", "SPX": "^GSPC", "DJI": "^DJI", 
        "WTX": "WTX=F", "TWII": "^TWII", "N225": "^N225", "KS11": "^KS11"
    }
    results = {}
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            df_daily = ticker.history(period="10d")
            if not df_daily.empty:
                valid = df_daily[df_daily['Close'] > 0].dropna()
                curr = valid['Close'].iloc[-1]
                prev = valid['Close'].iloc[-2]
                
                # 時間標註邏輯
                last_date = valid.index[-1].strftime('%m/%d')
                time_str = f"{last_date} 收盤"
                try:
                    df_min = ticker.history(period="1d", interval="1m")
                    if not df_min.empty:
                        last_time = df_min.index[-1].astimezone(pytz.timezone('Asia/Taipei'))
                        time_str = last_time.strftime('%m/%d %H:%M')
                except: pass
                
                results[name] = {"curr": curr, "prev": prev, "date": time_str}
        except:
            results[name] = {"curr": 0, "prev": 0, "date": "N/A"}
    return results

# --- UI 渲染 ---
st.title("🌎 全球多空情緒監控中心")
st.write(f"🕒 系統檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

fng = get_wantgoo_fng()
m_data = get_market_data()

# 第一排：核心情緒指標
st.subheader("🔥 核心情緒指標")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("恐懼與貪婪 (玩股網)", f"{fng['val']}", fng['text'])
    st.progress(fng['val'])
    st.caption("數據來源：玩股網 (同步 CNN)")

with c2:
    v = m_data.get("VIX", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("VIX 恐慌指數", f"{v['curr']:.2f}", f"{v['curr']-v['prev']:.2f}", delta_color="inverse")
    st.caption(f"📅 數據時間: {v['date']}")

with c3:
    pc = m_data.get("PCCR", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("CBOE Put/Call Ratio", f"{pc['curr']:.2f}", f"{pc['curr']-pc['prev']:.2f}", delta_color="inverse")
    st.caption(f"📅 數據時間: {pc['date']}")

st.divider()

# 第二排：美股市場 (納斯達克 -> 標普 -> 道瓊)
st.subheader("🏙️ 美股市場")
cu1, cu2, cu3 = st.columns(3)
with cu1:
    nas = m_data.get("NAS", {"curr":0, "prev":0, "date":"N/A"})
    pct = ((nas['curr']-nas['prev'])/nas['prev'])*100 if nas['prev']!=0 else 0
    st.metric("NASDAQ (小那)", f"{nas['curr']:.0f}", f"{pct:.2f}%")
    st.caption(f"📅 最後成交: {nas['date']}")
with cu2:
    sp = m_data.get("SPX", {"curr":0, "prev":0, "date":"N/A"})
    pct = ((sp['curr']-sp['prev'])/sp['prev'])*100 if sp['prev']!=0 else 0
    st.metric("S&P 500 (標普)", f"{sp['curr']:.0f}", f"{pct:.2f}%")
    st.caption(f"📅 最後成交: {sp['date']}")
with cu3:
    dji = m_data.get("DJI", {"curr":0, "prev":0, "date":"N/A"})
    pct = ((dji['curr']-dji['prev'])/dji['prev'])*100 if dji['prev']!=0 else 0
    st.metric("Dow Jones (道瓊)", f"{dji['curr']:.0f}", f"{pct:.2f}%")
    st.caption(f"📅 最後成交: {dji['date']}")

# 第三排：亞股市場 (台股第一)
st.subheader("🗾 亞股市場")
ca1, ca2, ca3 = st.columns(3)
with ca1:
    # 台股備援邏輯
    tw = m_data.get("WTX") if m_data.get("WTX", {}).get("curr", 0) > 0 else m_data.get("TWII", {"curr":0, "prev":0, "date":"N/A"})
    tw_diff = tw['curr'] - tw['prev']
    tw_pct = (tw_diff / tw['prev']) * 100 if tw['prev'] != 0 else 0
    st.metric("台股市場 (TW)", f"{tw['curr']:.0f}", f"{tw_diff:+.0f} ({tw_pct:+.2f}%)")
    st.caption(f"📅 精確時間: {tw['date']}")
with ca2:
    nk = m_data.get("N225", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("日經 225 (JP)", f"{nk['curr']:.0f}", f"{((nk['curr']-nk['prev'])/nk['prev'])*100:.2f}%")
    st.caption(f"📅 收盤時間: {nk['date']}")
with ca3:
    ks = m_data.get("KS11", {"curr":0, "prev":0, "date":"N/A"})
    st.metric("韓國 KOSPI (KR)", f"{ks['curr']:.2f}", f"{((ks['curr']-ks['prev'])/ks['prev'])*100:.2f}%")
    st.caption(f"📅 收盤時間: {ks['date']}")
