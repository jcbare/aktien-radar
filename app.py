import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

# --- SETUP TELEGRAM (Sicher aus den Secrets laden) ---
# Wir greifen jetzt auf den "Tresor" zu, statt den Token hier hinzuschreiben
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=payload)
    except Exception as e:
        pass

# --- 2. HILFSFUNKTIONEN ---
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
        return {"AAPL": "TR,REV", "TSLA": "TR,N26", "PLTR": "TR"}

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- 3. APP KONFIGURATION ---
st.set_page_config(page_title="Radar Pro", layout="wide")

# Ticker laden
t_map = load_tickers()
t_list = list(t_map.keys())

# --- 4. SEITENLEISTE (UI) ---
st.sidebar.header("⌚ Watch Setup")
watch_mode = st.sidebar.checkbox("Watch-Modus (Karten)", value=True)

if st.sidebar.button("🔔 Telegram Testen"):
    send_telegram_msg("<b>Test bestanden!</b> Dein Radar meldet sich jetzt auf der Watch. 🚀")
    st.sidebar.success("Test-Nachricht gesendet!")

st.sidebar.divider()
st.sidebar.header("Filter-Einstellungen")
min_growth = st.sidebar.slider("Mindest-Wachstum %", 0.0, 10.0, 2.0)
min_vol = st.sidebar.slider("Volumen-Faktor (Schnitt)", 1.0, 5.0, 1.5)
min_score_alert = st.sidebar.slider("Bot-Alarm ab Score %", 50, 100, 70)

# --- 5. HAUPTSEITE ---
st.title("🔮 Aktien-Radar Pro")

if st.button('🚀 SCAN STARTEN', use_container_width=True):
    status_text = st.empty()
    progress_circle = st.empty()
    
    try:
        with st.spinner('Lade aktuelle Marktdaten...'):
            # Batch-Download für alle Ticker gleichzeitig
            all_data = yf.download(t_list, period="40d", group_by='ticker', progress=False)
        
        results = []
        total = len(t_list)
        
        # Loop durch alle Aktien
        for i, t in enumerate(t_list):
            percent = (i + 1) / total
            
            # Animation alle 5 Ticker aktualisieren (für bessere Performance)
            if i % 5 == 0 or i == total - 1:
                status_text.markdown(f"<p style='text-align:center;'>Analysiere: <b>{t}</b> ({i+1}/{total})</p>", unsafe_allow_html=True)
                fig = go.Figure(go.Pie(
                    values=[percent, 1-percent],
                    hole=.8,
                    marker_colors=['#00FF00', '#222222'],
                    textinfo='none', showlegend=False, sort=False
                ))
                fig.update_layout(height=160, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)')
                progress_circle.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            try:
                # Daten für Ticker extrahieren
                df = all_data[t].dropna()
                if len(df) < 20: continue
                
                c_now = df['Close'].iloc[-1]
                growth = ((c_now - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                vol_today = df['Volume'].iloc[-1]
                vol_avg = df['Volume'].iloc[-21:-1].mean()
                vol_ratio = vol_today / vol_avg
                
                # Filter anwenden
                if growth >= min_growth and vol_ratio >= min_vol:
                    # Score-Berechnung (RSI + Close + Vol)
                    rsi = calculate_rsi(df['Close']).iloc[-1]
                    score = 0
                    if 50 < rsi < 75: score += 40
                    elif rsi >= 75: score += 10
                    
                    # Close-Stärke (nahe Tageshoch?)
                    day_range = df['High'].iloc[-1] - df['Low'].iloc[-1]
                    pos = (c_now - df['Low'].iloc[-1]) / day_range if day_range != 0 else 0
                    if pos > 0.8: score += 40
                    
                    # Volumen-Bestätigung
                    if vol_ratio > 2: score += 20
                    
                    # Ergebnisse speichern
                    res_entry = {
                        "Ticker": t, "Broker": t_map.get(t, "-"),
                        "Wachstum": growth, "Score": score, "Preis": c_now
                    }
                    results.append(res_entry)
                    
                    # PUSH-ALARM (Telegram)
                    if score >= min_score_alert:
                        msg = f"🚀 <b>ALARM: {t}</b>\nScore: {score}%\nWachstum: {growth:.1f}%\nPreis: {c_now:.2f}$\nBroker: {t_map.get(t)}"
                        send_telegram_msg(msg)
                        
            except:
                continue
        
        # Animation löschen
        status_text.empty()
        progress_circle.empty()

        # ERGEBNISSE ANZEIGEN
        if results:
            results = sorted(results, key=lambda x: x['Score'], reverse=True)
            st.success(f"Scan abgeschlossen. {len(results)} Signale gefunden.")
            
            if watch_mode:
                # Watch-Optimierte Karten (HTML)
                for res in results:
                    color = "#00FF00" if res['Score'] >= 70 else "#FFA500" if res['Score'] >= 40 else "#FF4B4B"
                    st.markdown(f"""
                    <div style="border: 1px solid #333; border-radius: 12px; padding: 12px; margin-bottom: 10px; border-left: 6px solid {color}; background-color: #0e1117;">
                        <div style="display: flex; justify-content: space-between; font-weight: bold; color: white;">
                            <span style="font-size: 18px;">{res['Ticker']}</span>
                            <span style="font-size: 18px;">{res['Preis']:.2f} $</span>
                        </div>
                        <div style="color: {color}; font-size: 22px; font-weight: bold; margin-top: 5px;">
                            Score: {res['Score']}%
                        </div>
                        <div style="font-size: 12px; color: #888; margin-top: 5px;">
                            Wachstum: {res['Wachstum']:.1f}% | {res['Broker']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                # Standard-Tabelle für Desktop
                st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning("Keine Treffer mit den aktuellen Filtern gefunden.")
            
    except Exception as e:
        st.error(f"Kritischer Fehler: {e}")
