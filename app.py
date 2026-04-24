import streamlit as st
import yfinance as yf
import pandas as pd

# --- APP KONFIGURATION ---
st.set_page_config(page_title="Broker-Radar 2026", layout="wide")

st.title("📱 Broker-Radar (N26, TR, Revolut)")
st.write("Scanne handelbare Wachstums-Werte nach Volumen-Anomalien.")

# --- FILTER ---
st.sidebar.header("Scan-Parameter")
min_growth = st.sidebar.slider("Wachstum heute (%)", 0.0, 20.0, 3.0)
min_vol = st.sidebar.slider("Volumen-Faktor (x-fach)", 1.0, 10.0, 2.0)
max_price = st.sidebar.number_input("Max. Preis (€/$)", value=500.0)

# --- FUNKTION: LOKALE DATEI LADEN ---
def load_local_tickers():
    try:
        with open("tickers.txt", "r") as f:
            content = f.read()
            # Entfernt Leerzeichen und teilt bei Kommas
            return [t.strip().upper() for t in content.replace("\n", "").split(",") if t.strip()]
    except:
        return ["AAPL", "TSLA", "NVDA"] # Notfall-Liste

ticker_list = load_local_tickers()
st.info(f"Scan-Bereit: {len(ticker_list)} Aktien aus deiner Broker-Liste.")

if st.button('🚀 Scan starten'):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, t in enumerate(ticker_list):
        status_text.text(f"Checke: {t}")
        try:
            # Schneller Check der letzten 5 Tage
            ticker_obj = yf.Ticker(t)
            hist = ticker_obj.history(period="5d")
            
            if len(hist) < 2: continue
            
            close_today = hist['Close'].iloc[-1]
            close_yesterday = hist['Close'].iloc[-2]
            vol_today = hist['Volume'].iloc[-1]
            vol_avg = hist['Volume'].iloc[:-1].mean()
            
            change = ((close_today - close_yesterday) / close_yesterday) * 100
            v_ratio = vol_today / vol_avg
            
            if change >= min_growth and v_ratio >= min_vol and close_today <= max_price:
                results.append({
                    "Ticker": t,
                    "Preis": f"{close_today:.2f}",
                    "Wachstum": f"{change:.2f}%",
                    "Volumen": f"{v_ratio:.1f}x"
                })
        except:
            pass
        
        progress_bar.progress((i + 1) / len(ticker_list))
    
    status_text.text("Scan beendet!")
    
    if results:
        st.success(f"{len(results)} Treffer gefunden!")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.warning("Keine Treffer. Versuche die Filter zu lockern.")
