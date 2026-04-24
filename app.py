import streamlit as st
import yfinance as yf
import pandas as pd

# --- APP KONFIGURATION ---
st.set_page_config(page_title="Multi-Timeframe Radar", layout="wide")

st.title("📈 Multi-Timeframe Radar")
st.markdown("Vergleiche das Wachstum über verschiedene Zeitspannen.")

# --- SEITENLEISTE ---
st.sidebar.header("Zeitspanne & Filter")

# NEU: Auswahl der Zeitspanne
timeframe = st.sidebar.selectbox(
    "Wachstum über welchen Zeitraum?",
    options=[1, 5, 10, 20],
    format_func=lambda x: f"{x} Handelstag(e)"
)

min_growth = st.sidebar.slider(f"Mindest-Wachstum über {timeframe} Tag(e) (%)", 0.0, 50.0, 5.0)
min_vol = st.sidebar.slider("Volumen-Faktor (nur heute)", 1.0, 10.0, 2.0)
max_price = st.sidebar.number_input("Max. Preis (€/$)", value=500.0)

# --- FUNKTION: TICKER & BROKER LADEN ---
def load_ticker_data():
    ticker_dict = {}
    try:
        with open("tickers.txt", "r") as f:
            for line in f:
                line = line.strip()
                if not line or "|" not in line: continue
                parts = line.split("|")
                sym = parts[0].strip().upper()
                ticker_dict[sym] = parts[1].strip()
        return ticker_dict
    except:
        return {"AAPL": "TR,N26,REV"}

ticker_map = load_ticker_data()
ticker_list = list(ticker_map.keys())

st.info(f"Scan-Bereit: {len(ticker_list)} Aktien geladen.")

if st.button('🚀 Analyse starten'):
    status_text = st.empty()
    status_text.text("Lade Marktdaten herunter...")
    
    try:
        # Wir laden 40 Tage, um auch bei 20-Tage-Wachstum genug Puffer zu haben
        all_data = yf.download(ticker_list, period="40d", interval="1d", group_by='ticker', progress=False)
        
        results = []
        progress_bar = st.progress(0)
        
        for i, t in enumerate(ticker_list):
            try:
                df = all_data[t]
                
                # Prüfen, ob wir genug Daten für den gewählten Zeitraum haben
                if df.empty or len(df) <= timeframe: continue
                
                # BERECHNUNG
                price_now = df['Close'].iloc[-1]
                price_then = df['Close'].iloc[-1 - timeframe] # Hier springen wir zurück!
                
                vol_today = df['Volume'].iloc[-1]
                vol_avg = df['Volume'].iloc[-21:-1].mean() # Durchschnitt der letzten 20 Tage vor heute
                
                growth = ((price_now - price_then) / price_then) * 100
                v_ratio = vol_today / vol_avg
                
                if growth >= min_growth and v_ratio >= min_vol and price_now <= max_price:
                    results.append({
                        "Ticker": t,
                        "Broker": ticker_map.get(t, "-"),
                        "Preis Aktuell": f"{price_now:.2f}",
                        f"Wachstum ({timeframe}d)": f"{growth:.2f}%",
                        "Volumen-Faktor": f"{v_ratio:.1f}x"
                    })
            except:
                continue
            
            progress_bar.progress((i + 1) / len(ticker_list))
            
        status_text.text("Scan abgeschlossen.")
        
        if results:
            st.success(f"{len(results)} Treffer gefunden!")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning(f"Keine Aktie mit +{min_growth}% über {timeframe} Tage gefunden.")
            
    except Exception as e:
        st.error(f"Fehler: {e}")

st.divider()
st.caption(f"Die Berechnung vergleicht den heutigen Preis mit dem Schlusskurs von vor {timeframe} Handelstagen.")
