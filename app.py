import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- APP KONFIGURATION ---
st.set_page_config(page_title="Radar Pro", layout="wide")

# CSS für echtes Watch-Design (Karten-Look)
st.markdown("""
    <style>
    .watch-card {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        border-left: 5px solid #00ff00;
    }
    .score-high { color: #00ff00; font-weight: bold; }
    .score-mid { color: #ffa500; font-weight: bold; }
    .score-low { color: #ff4b4b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- SEITENLEISTE ---
st.sidebar.header("Trading Setup")
watch_mode = st.sidebar.checkbox("⌚ Watch-Modus Optimierung", value=True)
timeframe = st.sidebar.selectbox("Zeitraum (Tage)", [1, 5, 10], index=0)
min_growth = st.sidebar.slider("Mindest-Wachstum %", 0.0, 20.0, 2.0)
min_vol = st.sidebar.slider("Volumen-Faktor", 1.0, 5.0, 1.5)

# --- FUNKTIONEN ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def load_ticker_data():
    try:
        ticker_dict = {}
        with open("tickers.txt", "r") as f:
            for line in f:
                if "|" in line:
                    parts = line.split("|")
                    ticker_dict[parts[0].strip().upper()] = parts[1].strip()
        return ticker_dict
    except: return {"AAPL": "TR,REV"}

ticker_map = load_ticker_data()
ticker_list = list(ticker_map.keys())

# --- HAUPTSEITE ---
if not watch_mode:
    st.title("🔮 Prognose-Radar")
else:
    st.markdown("<h2 style='text-align: center;'>🔮 RADAR</h2>", unsafe_allow_html=True)

if st.button('🚀 SCAN STARTEN', use_container_width=True):
    # Platzhalter für die Prozess-Animation
    progress_placeholder = st.empty()
    
    try:
        # Schnell-Download
        all_data = yf.download(ticker_list, period="40d", group_by='ticker', progress=False)
        results = []
        
        total = len(ticker_list)
        for i, t in enumerate(ticker_list):
            # KREIS-ANIMATION (PROZESS)
            percent = (i + 1) / total
            fig = go.Figure(go.Pie(
                values=[percent, 1-percent],
                hole=.75,
                marker_colors=['#00ff00', '#333333'],
                textinfo='none', showlegend=False, sort=False
            ))
            fig.update_layout(
                height=180, margin=dict(t=0, b=0, l=0, r=0),
                paper_bgcolor='rgba(0,0,0,0)',
                annotations=[dict(text=f"{int(percent*100)}%", x=0.5, y=0.5, font_size=24, font_color="white", showarrow=False)]
            )
            progress_placeholder.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            try:
                df = all_data[t].dropna()
                if len(df) < 20: continue
                
                c_now = df['Close'].iloc[-1]
                c_prev = df['Close'].iloc[-1-timeframe]
                growth = ((c_now - c_prev) / c_prev) * 100
                
                vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-21:-1].mean()
                
                if growth >= min_growth and vol_ratio >= min_vol:
                    # Score berechnen
                    rsi = calculate_rsi(df['Close']).iloc[-1]
                    score = 0
                    if 50 < rsi < 75: score += 40
                    elif rsi >= 75: score += 10
                    pos = (c_now - df['Low'].iloc[-1]) / (df['High'].iloc[-1] - df['Low'].iloc[-1]) if (df['High'].iloc[-1] - df['Low'].iloc[-1]) != 0 else 0
                    if pos > 0.8: score += 40
                    if vol_ratio > 2: score += 20
                    
                    results.append({
                        "ticker": t, "broker": ticker_map.get(t, "-"),
                        "growth": growth, "score": score, "price": c_now
                    })
            except: continue
            
        progress_placeholder.empty() # Animation nach Scan entfernen

        if results:
            results = sorted(results, key=lambda x: x['score'], reverse=True)
            for res in results:
                s_class = "score-high" if res['score'] >= 70 else "score-mid" if res['score'] >= 40 else "score-low"
                border_col = "#00ff00" if res['score'] >= 70 else "#ffa500" if res['score'] >= 40 else "#ff4b4b"
                
                # HTML CARD DESIGN
                st.markdown(f"""
                <div style="background-color: #1e1e1e; border-radius: 10px; padding: 12px; margin-bottom: 10px; border-left: 6px solid {border_col};">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-size: 18px; font-weight: bold; color: white;">{res['ticker']}</span>
                        <span style="font-size: 18px; color: white;">{res['price']:.2f}$</span>
                    </div>
                    <div style="margin-top: 5px;">
                        <span class="{s_class}" style="font-size: 20px;">Score: {res['score']}%</span>
                        <span style="color: #aaa; font-size: 14px; margin-left: 10px;">({res['growth']:.1f}%)</span>
                    </div>
                    <div style="font-size: 12px; color: #888; margin-top: 4px;">{res['broker']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Keine Treffer.")
            
    except Exception as e:
        st.error(f"Scan-Fehler: {e}")
