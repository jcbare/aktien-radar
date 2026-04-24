import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests # Neu für Telegram

# --- SETUP TELEGRAM ---
TELEGRAM_TOKEN = "8786526859:AAF5JZEiWJLf8qun1WWeyAeRzBG6AEXgCGg"
TELEGRAM_CHAT_ID = "1033631991"

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=payload)
    except:
        pass

# --- APP KONFIGURATION ---
st.set_page_config(page_title="Radar Pro + Bot", layout="wide")

# --- TICKER & FUNKTIONEN (Bleiben gleich) ---
def load_tickers():
    try:
        t_dict = {}
        with open("tickers.txt", "r") as f:
            for line in f:
                if "|" in line:
                    p = line.split("|")
                    t_dict[p[0].strip().upper()] = p[1].strip()
        return t_dict
    except: return {"AAPL": "TR,REV"}

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

t_map = load_tickers()
t_list = list(t_map.keys())

# --- UI ---
st.sidebar.header("Bot Einstellungen")
send_to_telegram = st.sidebar.checkbox("Push-Benachrichtigung an Uhr", value=True)
min_score_alert = st.sidebar.slider("Alarm ab Score %", 50, 100, 70)

st.title("🔮 Radar + Telegram")

if st.button('🚀 SCAN STARTEN', use_container_width=True):
    status_text = st.empty()
    progress_circle = st.empty()
    
    with st.spinner('Lade Börsendaten...'):
        all_data = yf.download(t_list, period="40d", group_by='ticker', progress=False)
    
    results = []
    total = len(t_list)
    
    for i, t in enumerate(t_list):
        percent = (i + 1) / total
        status_text.markdown(f"<p style='text-align:center;'>Checke {t}...</p>", unsafe_allow_html=True)
        
        # Kreis-Animation
        fig = go.Figure(go.Pie(values=[percent, 1-percent], hole=.8, marker_colors=['#00FF00', '#222222'], textinfo='none', showlegend=False, sort=False))
        fig.update_layout(height=150, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)')
        progress_circle.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        try:
            df = all_data[t].dropna()
            if len(df) < 20: continue
            c_now = df['Close'].iloc[-1]
            growth = ((c_now - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-21:-1].mean()
            
            if growth >= 1.0 and vol_ratio >= 1.2: # Beispiel-Filter
                rsi = calculate_rsi(df['Close']).iloc[-1]
                score = 0
                if 50 < rsi < 75: score += 40
                if (c_now - df['Low'].iloc[-1]) / (df['High'].iloc[-1] - df['Low'].iloc[-1]) > 0.8: score += 40
                if vol_ratio > 2: score += 20
                
                # TELEGRAM ALARM SENDEN
                if send_to_telegram and score >= min_score_alert:
                    msg = f"🚀 <b>ALARM: {t}</b>\nScore: {score}%\nWachstum: {growth:.1f}%\nPreis: {c_now:.2f}$\nBroker: {t_map.get(t)}"
                    send_telegram_msg(msg)
                
                results.append({"Ticker": t, "Score": score, "Preis": c_now})
        except: continue
        
    status_text.empty()
    progress_circle.empty()
    st.success(f"Scan fertig. {len(results)} Signale gefunden!")
