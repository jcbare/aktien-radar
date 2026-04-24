{\rtf1\ansi\ansicpg1252\cocoartf2639
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;\f1\fnil\fcharset0 AppleColorEmoji;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import yfinance as yf\
import pandas as pd\
\
# --- APP KONFIGURATION ---\
st.set_page_config(page_title="Aktien-Radar 2026", page_icon="
\f1 \uc0\u55357 \u56520 
\f0 ", layout="wide")\
\
st.title("
\f1 \uc0\u55357 \u56960 
\f0  Dein High-Growth Aktien-Radar")\
st.markdown("""\
Dieses Tool scannt Aktien nach **Wachstums-Explosionen** und **ungew\'f6hnlichem Handelsvolumen**. \
Ideal, um fr\'fchzeitig auf Ausbr\'fcche (wie bei Penny Stocks) aufmerksam zu werden.\
""")\
\
# --- SEITENLEISTE F\'dcR EINSTELLUNGEN ---\
st.sidebar.header("Filter-Einstellungen")\
\
# Hier stellst du dein "X %" Wachstum ein\
min_growth = st.sidebar.slider("Mindest-Wachstum heute (%)", 0.0, 50.0, 5.0)\
min_vol_factor = st.sidebar.slider("Volumen-Anomalie (x-facher Durchschnitt)", 1.0, 10.0, 3.0)\
max_price = st.sidebar.number_input("Maximaler Preis (\'80/$)", value=20.0)\
\
# --- AKTIENLISTE ---\
# Eine Mischung aus bekannten Wachstumserten und deutschen Small-Caps\
tickers = [\
    'AAPL', 'TSLA', 'NVDA', 'PLTR', 'NIO', 'MARA', 'RIOT', 'SNDL',  # US Growth\
    'A2AAE2.DE', 'DB1.DE', 'CBK.DE', 'VOW3.DE', 'MBG.DE', 'IFX.DE'   # DE & Beispiel-Penny-Stocks\
]\
\
if st.button('
\f1 \uc0\u55357 \u56960 
\f0  Markt jetzt scannen'):\
    st.write("Suche l\'e4uft... Bitte einen Moment Geduld.")\
    results = []\
    \
    progress_bar = st.progress(0)\
    \
    for index, t in enumerate(tickers):\
        try:\
            ticker_obj = yf.Ticker(t)\
            # Wir laden die Daten der letzten 20 Tage f\'fcr den Volumen-Durchschnitt\
            data = ticker_obj.history(period="20d")\
            \
            if len(data) < 5:\
                continue\
                \
            # Aktuelle Werte (heute)\
            current_close = data['Close'].iloc[-1]\
            last_close = data['Close'].iloc[-2]\
            current_vol = data['Volume'].iloc[-1]\
            \
            # Durchschnitts-Volumen der letzten 19 Tage\
            avg_vol = data['Volume'].iloc[:-1].mean()\
            \
            # Berechnungen\
            growth = ((current_close - last_close) / last_close) * 100\
            vol_ratio = current_vol / avg_vol\
            \
            # DER FILTER (Die Logik von der wir sprachen)\
            if growth >= min_growth and vol_ratio >= min_vol_factor and current_close <= max_price:\
                results.append(\{\
                    "Ticker": t,\
                    "Preis": f"\{current_close:.2f\}",\
                    "Wachstum (%)": f"\{growth:.2f\}%",\
                    "Volumen-Faktor": f"\{vol_ratio:.1f\}x",\
                    "Info": "
\f1 \uc0\u55357 \u56613 
\f0  Signal gefunden"\
                \})\
        except Exception as e:\
            pass # Fehler bei einzelnen Aktien ignorieren\
        \
        progress_bar.progress((index + 1) / len(tickers))\
\
    # --- ERGEBNIS-ANZEIGE ---\
    if results:\
        st.success(f"Gefunden: \{len(results)\} Treffer!")\
        df_res = pd.DataFrame(results)\
        st.dataframe(df_res, use_container_width=True)\
        \
        st.info("Tipp: Ein hoher Volumen-Faktor deutet oft auf institutionelles Interesse oder Insider-K\'e4ufe hin.")\
    else:\
        st.warning("Keine Aktie erf\'fcllt aktuell die Kriterien. Versuche, die Filter etwas lockerer einzustellen.")\
\
st.divider()\
st.caption("Datenquelle: Yahoo Finance (leicht verz\'f6gert). Dies ist keine Anlageberatung.")}