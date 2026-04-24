import streamlit as st
import yfinance as yf
import pandas as pd

# --- APP KONFIGURATION ---
st.set_page_config(page_title="Prognose-Radar 2026", layout="wide")

st.title("🔮 Prognose-Radar: Next-Day Momentum")
st.markdown("Dieses Tool berechnet Wahrscheinlichkeiten ohne externe Zusatz-Bibliotheken.")

# --- SEITENLEISTE ---
st.sidebar.header("Strategie-Parameter")
timeframe = st.sidebar.selectbox("Basis-Zeitraum für Wachstum", [1, 5, 10], index=0)
min_growth = st.sidebar.slider("Mindest-Wachstum (%)", 0.0, 30.0, 3.0)
min_vol = st.sidebar.slider("Volumen-Faktor", 1.0, 10.0, 2.0)

# --- FUNKTION: RSI MANUELL BERECHNEN ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- FUNKTION: SCORE BERECHNEN ---
def calculate_momentum_score(df):
    score = 0
    # 1. RSI Check
    rsi_series = calculate_rsi(df['Close'])
    rsi = rsi_series.iloc[-1]
    
    if 50 < rsi < 75: score += 40
    elif rsi >= 75: score += 10
    
    # 2. Strong Close Check
    day_high = df['High'].iloc[-1]
    day_low = df['Low'].iloc[-1]
    day_close = df['Close'].iloc[-1]
    
    pos = (day_close - day_low) / (day_high - day_low) if (day_high - day_low) != 0 else 0
    if pos > 0.8: score += 40
    elif pos > 0.5: score += 20
    
    # 3. Volumen
    vol_today = df['Volume'].iloc[-1]
    vol_avg = df['Volume'].iloc[-20:-1].mean()
    if vol_today > vol_avg * 3: score += 20
    elif vol_today > vol_avg * 1.5: score += 10
    
    return score, rsi

# --- TICKER LADEN ---
def load_ticker_data():
    ticker_dict = {}
    try:
        with open("tickers.txt", "r") as f:
            for line in f:
                line = line.strip()
                if "|" in line:
                    parts = line.split("|")
                    ticker_dict[parts[0].strip().upper()] = parts[1].strip()
        return ticker_dict
    except: return {"AAPL": "TR,N26,REV"}

ticker_map = load_ticker_data()
ticker_list = list(ticker_map.keys())

if st.button('🚀 Prognose-Scan starten'):
    status = st.empty()
    status.text("Lade Daten und berechne Prognose...")
    
    try:
        all_data = yf.download(ticker_list, period="40d", group_by='ticker', progress=False)
        results = []
        
        for t in ticker_list:
            try:
                df = all_data[t].dropna()
                if len(df) < 20: continue
                
                price_now = df['Close'].iloc[-1]
                price_prev = df['Close'].iloc[-1 - timeframe]
                growth = ((price_now - price_prev) / price_prev) * 100
                
                vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-21:-1].mean()
                
                if growth >= min_growth and vol_ratio >= min_vol:
                    score, rsi = calculate_momentum_score(df)
                    
                    if score >= 70: trend = "🟢 STARK"
                    elif score >= 40: trend = "🟡 NEUTRAL"
                    else: trend = "🔴 SCHWACH"
                    
                    results.append({
                        "Ticker": t,
                        "Broker": ticker_map.get(t, "-"),
                        "Wachstum": f"{growth:.1f}%",
                        "RSI": f"{rsi:.1f}" if not pd.isna(rsi) else "N/A",
                        "Score": f"{score}%",
                        "Prognose": trend
                    })
            except: continue
            
        status.text("Scan abgeschlossen.")
        if results:
            st.dataframe(pd.DataFrame(results).sort_values(by="Score", ascending=False), use_container_width=True)
        else:
            st.warning("Keine Treffer.")
            
    except Exception as e:
        st.error(f"Fehler: {e}")
