import yfinance as yf
import pandas as pd
import requests
import os

# --- SETUP TELEGRAM (Holt die Daten aus den GitHub Secrets) ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=payload)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- SCAN LOGIK ---
def run_scan():
    # Ticker laden
    t_dict = {}
    with open("tickers.txt", "r") as f:
        for line in f:
            if "|" in line:
                p = line.split("|")
                t_dict[p[0].strip().upper()] = p[1].strip()
    
    t_list = list(t_dict.keys())
    data = yf.download(t_list, period="40d", group_by='ticker', progress=False)
    
    for t in t_list:
        try:
            df = data[t].dropna()
            if len(df) < 20: continue
            
            c_now = df['Close'].iloc[-1]
            growth = ((c_now - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-21:-1].mean()
            
            # Filter: Wachstum > 2% und Volumen > 1.5
            if growth >= 2.0 and vol_ratio >= 1.5:
                rsi = calculate_rsi(df['Close']).iloc[-1]
                score = 0
                if 50 < rsi < 75: score += 40
                if (c_now - df['Low'].iloc[-1]) / (df['High'].iloc[-1] - df['Low'].iloc[-1]) > 0.8: score += 40
                if vol_ratio > 2: score += 20
                
                if score >= 70:
                    msg = f"🚀 <b>AUTO-ALARM: {t}</b>\nScore: {score}%\nWachstum: {growth:.1f}%\nPreis: {c_now:.2f}$\nBroker: {t_dict.get(t)}"
                    send_telegram_msg(msg)
        except:
            continue

if __name__ == "__main__":
    run_scan()
