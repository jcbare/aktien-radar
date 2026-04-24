import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- APP KONFIGURATION ---
st.set_page_config(page_title="Radar Pro", layout="wide")

# --- TICKER LADEN ---
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

# --- RSI BERECHNUNG (MANUELL FÜR STABILITÄT) ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

t_map = load_tickers()
t_list = list(t_map.keys())

st.title("🔮 Aktien-Radar")

# --- SEITENLEISTE ---
st.sidebar.header("Filter")
min_growth = st.sidebar.slider("Wachstum %", 0.0, 10.0, 2.0)
min_vol = st.sidebar.slider("Volumen-Faktor", 1.0, 5.0, 1.5)

if st.button('🚀 SCAN STARTEN', use_container_width=True):
    # --- ANIMATIONS-BEREICH ---
    status_text = st.empty()
    progress_circle = st.empty()
    
    try:
        with st.spinner('Verbinde mit Börsendaten...'):
            all_data = yf.download(t_list, period="40d", group_by='ticker', progress=False)
        
        results = []
        total = len(t_list)
        
        for i, t in enumerate(t_list):
            # Fortschritts-Animation aktualisieren
            percent = (i + 1) / total
            status_text.markdown(f"<p style='text-align:center;'>Suche in <b>{t}</b>... ({i+1}/{total})</p>", unsafe_allow_html=True)
            
            # Das Kreisdiagramm als Fortschrittsanzeige
            fig = go.Figure(go.Pie(
                values=[percent, 1-percent],
                hole=.8,
                marker_colors=['#00FF00', '#222222'],
                textinfo='none', showlegend=False, sort=False
            ))
            fig.update_layout(height=150, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)')
            progress_circle.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            try:
                df = all_data[t].dropna()
                if len(df) < 20: continue
                
                # Werte berechnen
                close_now = df['Close'].iloc[-1]
                growth = ((close_now - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-21:-1].mean()
                
                if growth >= min_growth and vol_ratio >= min_vol:
                    rsi = calculate_rsi(df['Close']).iloc[-1]
                    score = 0
                    if 50 < rsi < 75: score += 40
                    if (close_now - df['Low'].iloc[-1]) / (df['High'].iloc[-1] - df['Low'].iloc[-1]) > 0.8: score += 40
                    if vol_ratio > 2: score += 20
                    
                    results.append({"Ticker": t, "Broker": t_map.get(t, "-"), "Wachstum": growth, "Score": score, "Preis": close_now})
            except: continue
        
        # Nach dem Scan: Animationen entfernen
        status_text.empty()
        progress_circle.empty()

        if results:
            # ERGEBNISSE ANZEIGEN MIT FARBIGEN SCORES
            results = sorted(results, key=lambda x: x['Score'], reverse=True)
            
            for res in results:
                # Farblogik
                color = "#00FF00" if res['Score'] >= 70 else "#FFA500" if res['Score'] >= 40 else "#FF4B4B"
                
                # Anzeige als kompakte Info-Box (Perfekt für Watch & Mobile)
                st.markdown(f"""
                <div style="border: 1px solid #333; border-radius: 10px; padding: 10px; margin-bottom: 5px;">
                    <div style="display: flex; justify-content: space-between; font-weight: bold;">
                        <span>{res['Ticker']}</span>
                        <span>{res['Preis']:.2f} $</span>
                    </div>
                    <div style="color: {color}; font-size: 20px; font-weight: bold;">
                        Score: {res['Score']}%
                    </div>
                    <div style="font-size: 12px; color: #888;">
                        Wachstum: {res['Wachstum']:.1f}% | {res['Broker']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Keine Treffer gefunden.")
            
    except Exception as e:
        st.error(f"Fehler: {e}")
