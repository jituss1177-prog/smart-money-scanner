import streamlit as st
import yfinance as yf
import pandas as pd
import os

# Custom RSI formula
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Website ki Setting (Poori tarah se Stealth)
st.set_page_config(page_title="Smart Money", page_icon="🎯", layout="wide")
st.title("🎯 Smart Money")

if st.button("Run Scan 🚀"):
    file_path = "Trading_Symbols_Chartink.txt"
    stocks = []
    
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            stocks = [line.strip() + ".NS" for line in f.readlines() if line.strip()]
    else:
        st.error("Trading_Symbols_Chartink.txt file nahi mili. Kripya GitHub par check karein.")

    if stocks:
        with st.spinner("Processing list... please wait."):
            results = []
            progress_bar = st.progress(0)
            
            for i, stock in enumerate(stocks):
                progress_bar.progress((i + 1) / len(stocks))
                
                try:
                    data = yf.download(stock, period="120d", progress=False)
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.get_level_values(0)
                        
                    if len(data) >= 90:
                        data['RSI'] = compute_rsi(data['Close'], 14)
                        latest_rsi = float(data['RSI'].iloc[-1])
                        
                        # Filter 1: RSI 35 ya usse niche
                        if latest_rsi <= 35:
                            data['Avg_Vol_20'] = data['Volume'].rolling(window=20).mean()
                            last_7_days = data.tail(7)
                            
                            accumulation_found = False
                            entry_date = ""
                            
                            # Filter 2: Stealth Accumulation Check karna
                            for date, row in last_7_days.iterrows():
                                open_p = float(row['Open'])
                                close_p = float(row['Close'])
                                high_p = float(row['High'])
                                low_p = float(row['Low'])
                                
                                body = abs(open_p - close_p)
                                lower_wick = min(open_p, close_p) - low_p
                                total_range = high_p - low_p
                                
                                # Absorption Logic: Price niche gaya par niche ki wick body se badi hai
                                if total_range > 0 and lower_wick > body and (lower_wick / total_range) >= 0.4:
                                    accumulation_found = True
                                    entry_date = date.strftime("%d %b %Y") # Date nikalna
                                    break
                            
                            if accumulation_found:
                                symbol_clean = stock.replace(".NS", "")
                                tv_link = f"https://in.tradingview.com/chart/?symbol=NSE:{symbol_clean}"
                                current_close = float(data['Close'].iloc[-1])
                                
                                results.append({
                                    "Stock": symbol_clean,
                                    "Entry Date": entry_date,
                                    "Current Price": round(current_close, 2),
                                    "RSI": round(latest_rsi, 2),
                                    "Open in TradingView": tv_link
                                })
                except Exception as e:
                    pass
            
            progress_bar.empty()

            if len(results) > 0:
                df = pd.DataFrame(results)
                
                st.dataframe(
                    df,
                    column_config={
                        "Open in TradingView": st.column_config.LinkColumn(
                            "Open in TradingView", display_text="View Chart 📈"
                        )
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No records found.")
