import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- SETUP & INITIALISIERUNG ---
analyzer = SentimentIntensityAnalyzer()

# Falls du die Secrets für Telegram auch hier nutzt:
try:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except:
    TELEGRAM_TOKEN = None

def send_telegram_msg(message):
    if TELEGRAM_TOKEN:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=payload)

def get_sentiment_data(ticker_obj):
    try:
        news = ticker_obj.news
        if not news: return 0, "Keine News"
        combined_text = ". ".join([item['title'] for item in news[:3]])
        vs = analyzer.polarity_scores(combined_text)
        return vs['compound'], "\n".join([f"• {n['title']}" for n in news[:3]])
    except:
        return 0, "Fehler"

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- APP KONFIGURATION ---
st.set_page_config(page_title="Radar Pro", layout="wide")

def load_tickers():
    try:
        t_dict = {}
        with open("tickers.txt", "r") as f:
            for line in f:
                if "|" in line:
                    p = line.split("|")
                    t_dict[p[0].strip().upper()] = p[1].strip()
        return t_dict
    except:
        return {"AAPL": "TR,REV"}

t_map = load_tickers()
t_list = list(t_map.keys())

# --- UI SEITENLEISTE ---
st.sidebar.header("⚙️ Einstellungen")
watch_mode = st.sidebar.checkbox("⌚ Watch-Modus Optimierung", value=True)
min_score_alert = st.sidebar.slider("Alarm ab Score %", 50, 100, 70)

# --- HAUPTSEITE ---
st.title("🔮 Aktien-Radar Pro")

if st.button('🚀 SCAN STARTEN', use_container_width=True):
    status_text = st.empty()
    progress_circle = st.empty()
    
    with st.spinner('Lade Marktdaten...'):
        all_data = yf.download(t_list, period="40d", group_by='ticker', progress=False)
    
    results = []
    total = len(t_list)
    
    for i, t in enumerate(t_list):
        percent = (i + 1) / total
        if i % 5 == 0:
            status_text.markdown(f"<p style='text-align:center;'>Checke {t}...</p>", unsafe_allow_html=True)
            fig = go.Figure(go.Pie(values=[percent, 1-percent], hole=.8, marker_colors=['#00FF00', '#222222'], textinfo='none', showlegend=False, sort=False))
            fig.update_layout(height=150, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)')
            progress_circle.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        try:
            df = all_data[t].dropna()
            if len(df) < 20: continue
            c_now = df['Close'].iloc[-1]
            growth = ((c_now - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-21:-1].mean()
            
            if growth >= 1.0 and vol_ratio >= 1.2:
                rsi = calculate_rsi(df['Close']).iloc[-1]
                score = 0
                if 50 < rsi < 75: score += 40
                if (c_now - df['Low'].iloc[-1]) / (df['High'].iloc[-1] - df['Low'].iloc[-1]) > 0.8: score += 40
                if vol_ratio > 2: score += 20
                
                # ZUSATZDATEN FÜR TOP TREFFER
                isin_val = "N/A"
                sentiment_label = "Neutral"
                if score >= 70:
                    ticker_obj = yf.Ticker(t)
                    # ISIN mit zwei Versuchen holen
                    try:
                        # Weg 1: Direkter Schnellzugriff
                        isin_raw = ticker_obj.isin
                        
                        # Weg 2: Falls Weg 1 leer ist, aus den Info-Daten (gründlicher)
                        if not isin_raw or isin_raw == "-":
                            isin_raw = ticker_obj.get_info().get('isin')
                            
                        isin_val = str(isin_raw) if isin_raw and isin_raw != "-" else "Nicht gefunden"
                    except: 
                        isin_val = "Momentan n.v." # Falls Yahoo den Zugriff drosselt

                    # Sentiment holen
                    sent_val, _ = get_sentiment_data(ticker_obj)
                    if sent_val > 0.15: sentiment_label = "Positiv 🟢"
                    elif sent_val < -0.15: sentiment_label = "Negativ 🔴"

                results.append({
                    "Ticker": t, "Broker": t_map.get(t, "-"), "Wachstum": growth, 
                    "Score": score, "Preis": c_now, "ISIN": isin_val, "Sent": sentiment_label
                })
        except: continue
        
    status_text.empty()
    progress_circle.empty()

    if results:
        results = sorted(results, key=lambda x: x['Score'], reverse=True)
        for res in results:
            color = "#00FF00" if res['Score'] >= 70 else "#FFA500" if res['Score'] >= 40 else "#FF4B4B"
            
            # KARTEN-DESIGN MIT ISIN
            st.markdown(f"""
            <div style="border: 1px solid #333; border-radius: 12px; padding: 15px; margin-bottom: 10px; border-left: 6px solid {color}; background-color: #0e1117;">
                <div style="display: flex; justify-content: space-between; font-weight: bold; color: white;">
                    <span style="font-size: 20px;">{res['Ticker']}</span>
                    <span style="font-size: 20px;">{res['Preis']:.2f} $</span>
                </div>
                <div style="color: {color}; font-size: 24px; font-weight: bold; margin-top: 5px;">
                    Score: {res['Score']}%
                </div>
                <div style="font-size: 14px; color: #aaa; margin-top: 8px;">
                    <b>ISIN:</b> <code style="color: #00FF00;">{res['ISIN']}</code><br>
                    <b>Stimmung:</b> {res['Sent']}<br>
                    <span style="font-size: 12px;">Wachstum: {res['Wachstum']:.1f}% | {res['Broker']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
