import streamlit as st
import yfinance as yf
import pandas as pd

# --- APP KONFIGURATION ---
st.set_page_config(page_title="Broker-Radar 2026", layout="wide")

st.title("📱 Broker-Radar: Wo kann ich kaufen?")
st.markdown("Dieser Scanner zeigt dir direkt an, ob ein Fund bei **TR, N26 oder Revolut** handelbar ist.")

# --- SEITENLEISTE ---
st.sidebar.header("Filter-Einstellungen")
min_growth = st.sidebar.slider("Wachstum heute (%)", 0.0, 20.0, 2.0)
min_vol = st.sidebar.slider("Volumen-Faktor (Anomalie)", 1.0, 10.0, 2.0)
max_price = st.sidebar.number_input("Max. Preis (€/$)", value=1000.0)

# --- FUNKTION: TICKER & BROKER LADEN ---
def load_ticker_data():
    ticker_dict = {}
    try:
        with open("tickers.txt", "r") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                
                # Wenn ein | vorhanden ist, trennen wir Ticker und Broker
                if "|" in line:
                    parts = line.split("|")
                    sym = parts[0].strip().upper()
                    broker = parts[1].strip()
                    ticker_dict[sym] = broker
                else:
                    # Falls kein | da ist, schreiben wir "Alle?"
                    ticker_dict[line.upper()] = "Unbekannt"
        return ticker_dict
    except Exception as e:
        st.error(f"Fehler beim Laden der Datei: {e}")
        return {"AAPL": "TR,N26,REV"}

ticker_map = load_ticker_data()
ticker_list = list(ticker_map.keys())

st.info(f"Scan-Bereit: {len(ticker_list)} beobachtete Aktien.")

if st.button('🚀 Suche starten'):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, t in enumerate(ticker_list):
        status_text.text(f"Analysiere: {t}...")
        try:
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
                    "Broker": ticker_map.get(t, "-"), # Hier holen wir die Broker-Info
                    "Preis": f"{close_today:.2f}",
                    "Wachstum": f"{change:.2f}%",
                    "Volumen-Faktor": f"{v_ratio:.1f}x"
                })
        except:
            pass
        
        progress_bar.progress((i + 1) / len(ticker_list))
    
    status_text.text("Scan abgeschlossen.")
    
    if results:
        st.success(f"{len(results)} Treffer gefunden!")
        # Wir zeigen die Tabelle an und heben die Broker-Spalte hervor
        df_res = pd.DataFrame(results)
        st.dataframe(df_res, use_container_width=True)
    else:
        st.warning("Keine Treffer. Tipp: Setze das Wachstum auf 1% oder 2%, um die Funktion zu testen.")
