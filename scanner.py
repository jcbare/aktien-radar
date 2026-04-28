if score >= 70:
                    ticker_obj = yf.Ticker(t)
                    
                    # 1. ISIN mit sicherem Fallback
                    try:
                        isin_raw = ticker_obj.isin
                        isin_final = str(isin_raw) if isin_raw and isin_raw != "-" else "Nicht gefunden"
                    except:
                        isin_final = "Fehler beim Abruf"
                    
                    # 2. News & Sentiment abrufen
                    sentiment, news_headlines = get_sentiment_data(ticker_obj)
                    
                    # Sentiment-Icon festlegen
                    s_icon = "⚪"
                    if sentiment > 0.15: s_icon = "🟢"
                    elif sentiment < -0.15: s_icon = "🔴"

                    # 3. Das finale Nachrichten-Paket für Telegram
                    msg = (
                        f"🚀 <b>SIGNAL: {t}</b>\n"
                        f"🆔 ISIN: <code>{isin_final}</code>\n"
                        f"📊 Score: <b>{score}%</b>\n"
                        f"💰 Preis: {c_now:.2f}$\n"
                        f"🏢 Broker: {t_dict.get(t, '-')}\n"
                        f"🧠 Stimmung: {s_icon}\n"
                        f"------------------------\n"
                        f"📰 <b>Top News:</b>\n{news_headlines}"
                    )
                    
                    send_telegram_msg(msg)
