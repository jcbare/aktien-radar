import streamlit as st
import yfinance as yf
import pandas as pd

# --- APP KONFIGURATION ---
st.set_page_config(page_title="Profi-Radar 2026", page_icon="🔍", layout="wide")

st.title("🔍 Deep-Scan: High-Growth Radar")
st.markdown("Wir scannen jetzt ein größeres Universum nach Volatilität und Volumen.")

# --- SEITENLEISTE ---
st.sidebar.header("Filter-Einstellungen")
min_growth = st.sidebar.slider("Mindest-Wachstum heute (%)", 0.0, 30.0, 3.0)
min_vol_factor = st.sidebar.slider("Volumen-Faktor (x-fach)", 1.0, 10.0, 2.5)
max_price = st.sidebar.number_input("Maximaler Preis (€/$)", value=15.0)

# --- TICKER-QUELLE ---
st.subheader("Aktien-Auswahl")
ticker_input = st.text_area(
    "Ticker-Symbole (mit Leerzeichen oder Komma getrennt)", 
    value="MARA, RIOT, PLTR, NIO, DNA, SOFI, AI, BBAI, SOUN, GME, AMC, SNDL, TLRY, ACB, OGI, GRWG, HYLN, WKHS, NKLA, QS, CHPT, EVGO, RUN, SPWR, FSLR"
)

# Automatische Aufbereitung der Liste
tickers = [t.strip().upper() for t in ticker_input.replace(",", " ").split()]

if st.button('🚀 Intensiv-Scan starten'):
    st.write(f"Scanne {len(tickers)} Unternehmen...")
    results = []
    progress_bar = st.progress(0)
    
    for index, t in enumerate(tickers):
        try:
            # Wir nutzen 'period=2d', das geht schneller beim Scannen
            ticker_obj = yf.Ticker(t)
            data = ticker_obj.history(period="20d")
            
            if len(data) < 5: continue
                
            current_close = data['Close'].iloc[-1]
            last_close = data['Close'].iloc[-2]
            current_vol = data['Volume'].iloc[-1]
            avg_vol = data['Volume'].iloc[:-1].mean()
            
            growth = ((current_close - last_close) / last_close) * 100
            vol_ratio = current_vol / avg_vol
            
            # Die Logik
            if growth >= min_growth and vol_ratio >= min_vol_factor and current_close <= max_price:
                results.append({
                    "Ticker": t,
                    "Preis": f"{current_close:.2f}",
                    "Wachstum": f"{growth:.2f}%",
                    "Volumen-Faktor": f"{vol_ratio:.1f}x",
                    "Tag": data.index[-1].strftime('%Y-%m-%d')
                })
        except:
            pass
        
        progress_bar.progress((index + 1) / len(tickers))

    if results:
        st.success(f"Gefunden: {len(results)} Treffer!")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.warning("Keine Treffer. Tipp: Verringere das 'Mindest-Wachstum' oder erweitere die Ticker-Liste.")

st.divider()
st.info("💡 Profi-Tipp: Kopiere Ticker-Listen von Seiten wie 'Finviz Top Gainers' und füge sie oben ein.")
