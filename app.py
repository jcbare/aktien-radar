import streamlit as st
import yfinance as yf
import pandas as pd

# --- APP KONFIGURATION ---
st.set_page_config(page_title="Aktien-Radar 2026", page_icon="📈", layout="wide")

st.title("🚀 Dein High-Growth Aktien-Radar")
st.markdown("""
Dieses Tool scannt Aktien nach **Wachstums-Explosionen** und **ungewöhnlichem Handelsvolumen**. 
Ideal, um frühzeitig auf Ausbrüche aufmerksam zu werden.
""")

# --- SEITENLEISTE FÜR EINSTELLUNGEN ---
st.sidebar.header("Filter-Einstellungen")

min_growth = st.sidebar.slider("Mindest-Wachstum heute (%)", 0.0, 50.0, 5.0)
min_vol_factor = st.sidebar.slider("Volumen-Anomalie (x-facher Durchschnitt)", 1.0, 10.0, 3.0)
max_price = st.sidebar.number_input("Maximaler Preis (€/$)", value=20.0)

# --- AKTIENLISTE ---
tickers = [
    'AAPL', 'TSLA', 'NVDA', 'PLTR', 'NIO', 'MARA', 'RIOT', 'SNDL',
    'A2AAE2.DE', 'DB1.DE', 'CBK.DE', 'VOW3.DE', 'MBG.DE', 'IFX.DE'
]

if st.button('🚀 Markt jetzt scannen'):
    st.write("Suche läuft... Bitte einen Moment Geduld.")
    results = []
    progress_bar = st.progress(0)
    
    for index, t in enumerate(tickers):
        try:
            ticker_obj = yf.Ticker(t)
            data = ticker_obj.history(period="20d")
            
            if len(data) < 5:
                continue
                
            current_close = data['Close'].iloc[-1]
            last_close = data['Close'].iloc[-2]
            current_vol = data['Volume'].iloc[-1]
            avg_vol = data['Volume'].iloc[:-1].mean()
            
            growth = ((current_close - last_close) / last_close) * 100
            vol_ratio = current_vol / avg_vol
            
            if growth >= min_growth and vol_ratio >= min_vol_factor and current_close <= max_price:
                results.append({
                    "Ticker": t,
                    "Preis": f"{current_close:.2f}",
                    "Wachstum (%)": f"{growth:.2f}%",
                    "Volumen-Faktor": f"{vol_ratio:.1f}x",
                    "Info": "🔥 Signal gefunden"
                })
        except:
            pass
        
        progress_bar.progress((index + 1) / len(tickers))

    if results:
        st.success(f"Gefunden: {len(results)} Treffer!")
        df_res = pd.DataFrame(results)
        st.dataframe(df_res, use_container_width=True)
    else:
        st.warning("Keine Aktie erfüllt aktuell die Kriterien.")

st.divider()
st.caption("Datenquelle: Yahoo Finance. Keine Anlageberatung.")
