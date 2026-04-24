import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go # Für das Kreisdiagramm
import time

# --- APP KONFIGURATION ---
st.set_page_config(page_title="Watch Radar Pro", layout="wide")

# --- SEITENLEISTE ---
st.sidebar.header("Einstellungen")
watch_mode = st.sidebar.checkbox("⌚ Watch-Modus", value=False)
timeframe = st.sidebar.selectbox("Zeitraum (Tage)", [1, 5, 10], index=0)
min_growth = st.sidebar.slider("Wachstum (%)", 0.0, 30.0, 3.0)
min_vol = st.sidebar.slider("Volumen-Faktor", 1.0, 10.0, 2.0)

# --- FUNKTIONEN ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_momentum_score(df):
    rsi_series = calculate_rsi(df['Close'])
    rsi = rsi_series.iloc[-1]
    score = 0
    if 50 < rsi < 75: score += 40
    elif rsi >= 75: score += 10
    day_high, day_low, day_close = df['High'].iloc[-1], df['Low'].iloc[-1], df['Close'].iloc[-1]
    pos = (day_close - day_low) / (day_high - day_low) if (day_high - day_low) != 0 else 0
    if pos > 0.8: score += 40
    elif pos > 0.5: score += 20
    vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-20:-1].mean()
    if vol_ratio > 3: score += 20
    elif vol_ratio > 1.5: score += 10
    return score, rsi, vol_ratio

def load_ticker_data():
    try:
        ticker_dict = {}
        with open("tickers.txt", "r") as f:
            for line in f:
                if "|" in line:
                    parts = line.split("|")
                    ticker_dict[parts[0].strip().upper()] = parts[1].strip()
        return ticker_dict
    except: return {"AAPL": "TR"}

ticker_map = load_ticker_data()
ticker_list = list(ticker_map.keys())

# --- ANIMATIONS-HELFER (DIE SANDUHR) ---
def get_hourglass_frame(frame_num):
    frames = ["⏳", "⌛"]
    return frames[frame_num % 2]

# --- HAUPTSEITE ---
st.title("🔮 " + ("Radar" if not watch_mode else ""))

if st.button('🚀 SCAN STARTEN'):
    # Platzhalter für die Animationen
    anim_place = st.empty()
    chart_place = st.empty()
    
    try:
        # Batch-Download
        all_data = yf.download(ticker_list, period="40d", group_by='ticker', progress=False)
        results = []
        
        total = len(ticker_list)
        for i, t in enumerate(ticker_list):
            # 1. Sanduhr-Animation aktualisieren
            anim_place.markdown(f"## {get_hourglass_frame(i)} Analysiere {t}...")
            
            # 2. Kreisdiagramm (Progress) aktualisieren
            progress = (i + 1) / total
            fig = go.Figure(go.Pie(
                values=[progress, 1-progress],
                hole=.7,
                marker_colors=['#00FF00', '#222222'],
                textinfo='none',
                showlegend=False
            ))
            fig.update_layout(height=150, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)')
            chart_place.plotly_chart(fig, use_container_width=False)

            try:
                df = all_data[t].dropna()
                if len(df) < 20: continue
                change = ((df['Close'].iloc[-1] - df['Close'].iloc[-1-timeframe]) / df['Close'].iloc[-1-timeframe]) * 100
                score, rsi, v_ratio = calculate_momentum_score(df)
                if change >= min_growth and v_ratio >= min_vol:
                    results.append({"t": t, "b": ticker_map.get(t, "-"), "g": f"{change:.1f}%", "s": score, "p": df['Close'].iloc[-1]})
            except: continue

        # Nach dem Scan: Platzhalter leeren
        anim_place.empty()
        chart_place.empty()
        
        if results:
            results = sorted(results, key=lambda x: x['s'], reverse=True)
            if watch_mode:
                for res in results:
                    color = "green" if res['s'] >= 70 else "orange" if res['s'] >= 40 else "red"
                    st.markdown(f"--- \n ### **{res['t']}** | {res['p']:.2f}$ \n **Score: :{color}[{res['s']}%]** | {res['g']} \n *{res['b']}*")
            else:
                st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning("Keine Treffer.")
            
    except Exception as e:
        st.error(f"Fehler: {e}")
