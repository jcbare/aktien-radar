import streamlit as st
import yfinance as yf
import pandas as pd
import time

st.set_page_config(page_title="Deep-Scan 2026", layout="wide")

st.title("🌊 Deep-Ocean Scanner")
st.write("Suche in den großen Indizes nach den Nadeln im Heuhaufen.")

# --- FILTER ---
st.sidebar.header("Scan-Parameter")
index_choice = st.sidebar.selectbox("Welchen Markt scannen?", ["S&P 500 (US Tech & Industrie)", "NASDAQ 100 (Tech-Giganten)"])
min_growth = st.sidebar.slider("Wachstum (%)", 0.0, 20.0, 4.0)
min_vol = st.sidebar.slider("Volumen-Faktor", 1.0, 10.0, 2.0)

# --- FUNKTION: TICKER AUTOMATISCH LADEN ---
@st.cache_data # Das sorgt dafür, dass die Liste nicht bei jedem Klick neu geladen wird
def get_ticker_list(choice):
    if choice == "S&P 500 (US Tech & Industrie)":
        # Lädt die Liste direkt von Wikipedia (Standard-Trick für Trader)
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        table = pd.read_html(url)
        return table[0]['Symbol'].tolist()
    else:
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        table = pd.read_html(url)
        # In Wikipedia ist das die zweite Tabelle (Index 4)
        return table[4]['Ticker'].tolist()

ticker_list = get_ticker_list(index_choice)
st.info(f"Bereit zum Scannen von {len(ticker_list)} Unternehmen aus dem {index_choice}.")

if st.button('🔥 Großen Markte-Scan starten'):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Wir scannen in 10er-Blöcken, um Yahoo nicht zu "ärgern"
    for i, t in enumerate(ticker_list):
        status_text.text(f"Analysiere: {t} ({i+1}/{len(ticker_list)})")
        try:
            # Schneller Abruf: nur die letzten 2 Tage
            s = yf.Ticker(t)
            hist = s.history(period="20d")
            
            if len(hist) < 2: continue
            
            close_today = hist['Close'].iloc[-1]
            close_yesterday = hist['Close'].iloc[-2]
            vol_today = hist['Volume'].iloc[-1]
            vol_avg = hist['Volume'].iloc[:-1].mean()
            
            change = ((close_today - close_yesterday) / close_yesterday) * 100
            v_ratio = vol_today / vol_avg
            
            if change >= min_growth and v_ratio >= min_vol:
                results.append({
                    "Ticker": t,
                    "Preis": f"{close_today:.2f}$",
                    "Wachstum": f"{change:.2f}%",
                    "Volumen": f"{v_ratio:.1f}x"
                })
        except:
            pass
        
        progress_bar.progress((i + 1) / len(ticker_list))
    
    status_text.text("Scan abgeschlossen!")
    
    if results:
        st.balloons() # Kleiner Erfolgseffekt
        st.success(f"{len(results)} Nadeln im Heuhaufen gefunden!")
        st.table(pd.DataFrame(results))
    else:
        st.warning("Keine Treffer mit diesen harten Filtern.")
