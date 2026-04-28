if score >= 70:
                    ticker_obj = yf.Ticker(t)
                    
                    # ISIN Abfrage mit Fallback
                    isin_data = ticker_obj.isin
                    
                    # Falls yfinance 'None' oder ein leeres Objekt liefert
                    if isin_data is None or isin_data == "" or isin_data == "-":
                        isin_final = "ISIN nicht gefunden"
                    else:
                        isin_final = str(isin_data)
                    
                    # News Sentiment abrufen
                    sentiment, news_headlines = get_sentiment_data(ticker_obj)
                    
                    # ... Rest der Logik (Sentiment Icons etc.)
                    
                    # Die Nachricht (hier ISIN sicher einbauen)
                    msg = (
                        f"🚀 <b>SIGNAL: {t}</b>\n"
                        f"🆔 ISIN: <code>{isin_final}</code>\n"
                        f"📊 Score: <b>{score}%</b>\n"
                        f"💰 Preis: {c_now:.2f}$\n"
                        f"🏢 Broker: {t_dict.get(t)}\n"
                        f"🧠 Sentiment: {sentiment_label}\n\n"
                        f"📰 <b>Top News:</b>\n{news_headlines}"
                    )
                    send_telegram_msg(msg)
