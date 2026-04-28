import yfinance as yf
import pandas as pd
import requests
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- SETUP ---
# Holt die Daten sicher aus den GitHub Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
analyzer = SentimentIntensityAnalyzer()

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload)
    except:
        pass

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_sentiment_data(ticker_obj):
    """Analysiert die Schlagzeilen und gibt Score + Top-News zurück"""
    try:
        news = ticker_obj.news
        if not news:
            return 0, "Keine News gefunden"
            
        combined_text = ""
        headline_list = []
        for item in news[:3]: # Die Top 3 News
            combined_text += item['title'] + ". "
            headline_list.append(f"• {item['title']}")
            
        vs = analyzer.polarity_scores(combined_text)
        sentiment_score = vs['compound'] # Bereich -1 bis +1
        headlines_text = "\n".join(headline_list)
        return sentiment_score, headlines_text
    except:
        return 0, "News-Fehler"

# --- HAUPTFUNKTION ---
def run_scan():
    # Ticker-Liste laden
    t_dict = {}
    with open("tickers.txt", "r") as f:
        for line in f:
            if "|" in line:
                p = line.split("|")
                t_dict[p[0].strip().upper()] = p[1].strip()
    
    t_list = list(t_dict.keys())
    
    # Massen-Download der Kurse
    data = yf.download(t_list, period="40d", group_by='ticker', progress=False)
    
    for t in t_list:
        try:
            df = data[t].dropna()
            if len(df) < 20: continue
            
            c_now = df['Close'].iloc[-1]
            growth = ((c_now - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-21:-1].mean()
            
            # Basis-Filter (technisches Momentum)
            if growth >= 1.5 and vol_ratio >= 1.2:
                rsi = calculate_rsi(df['Close']).iloc[-1]
                
                # Scoring Logik
                score = 0
                if 50 < rsi < 75: score += 40
                if (c_now - df['Low'].iloc[-1]) / (df['High'].iloc[-1] - df['Low'].iloc[-1]) > 0.8: score += 40
                if vol_ratio > 2: score += 20
                
                # Nur bei starken technischen Signalen die "teuren" Daten (ISIN/News) laden
                if score >= 70:
                    ticker_obj = yf.Ticker(t)
                    
                    # 1. ISIN abrufen
                    isin = ticker_obj.isin
                    if not isin or isin == "-":
                        isin = "Nicht verfügbar"
                    
                    # 2. News Sentiment abrufen
                    sentiment, news_headlines = get_sentiment_data(ticker_obj)
                    
                    # Sentiment-Bonus/Abzug
                    sentiment_label = "Neutral ⚪"
                    if sentiment > 0.2:
                        score += 10
                        sentiment_label = "Positiv 🟢"
                    elif sentiment < -0.2:
                        score -= 30
                        sentiment_label = "VORSICHT/Negativ 🔴"

                    # Nachricht zusammenstellen
                    msg = (
                        f"🚀 <b>SIGNAL: {t}</b>\n"
                        f"🆔 ISIN: <code>{isin}</code>\n"
                        f"📊 Score: <b>{score}%</b>\n"
                        f"💰 Preis: {c_now:.2f}$\n"
                        f"🏢 Broker: {t_dict.get(t)}\n"
                        f"🧠 Sentiment: {sentiment_label}\n\n"
                        f"📰 <b>Top News:</b>\n{news_headlines}"
                    )
                    send_telegram_msg(msg)
        except Exception as e:
            continue

if __name__ == "__main__":
    run_scan()
