import streamlit as st
import yfinance as yf
import pandas as pd
import os

# Website ki Setting - Naya Title aur Icon
st.set_page_config(page_title="Smart Money", page_icon="🎯", layout="wide")
st.title("🎯 Smart Money Scanner")

# Ek hi button mein poora system
if st.button("Run Scan 🚀"):
    file_path = "Trading_Symbols_Chartink.txt"
    stocks = []
    
    # Text file se stocks load karna
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            stocks = [line.strip() + ".NS" for line in f.readlines() if line.strip()]
    else:
        st.error("Trading_Symbols_Chartink.txt file nahi mili. Kripya GitHub par check karein.")

    if stocks:
        with st.spinner("Processing list... please wait (takes 1-2 minutes for 600 stocks)"):
            results = []
            
            # Loading Bar
            progress_bar = st.progress(0)
            
            for i, stock in enumerate(stocks):
                progress_bar.progress((i + 1) / len(stocks))
                
                try:
                    data = yf.download(stock, period="30d", progress=False)
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.get_level_values(0)
                        
                    if len(data) >= 20:
                        data['Avg_Vol_20'] = data['Volume'].rolling(window=20).mean()
                        
                        # Pichle 7 din ka data check karna
                        last_7_days = data.tail(7)
                        
                        for date, row in last_7_days.iterrows():
                            open_p = float(row['Open'])
                            close_p = float(row['Close'])
                            vol = float(row['Volume'])
                            avg_vol = float(row['Avg_Vol_20'])
                            
                            # Logic: Green Candle + High Volume
                            is_green = close_p > open_p
                            vol_spike = vol / avg_vol if avg_vol > 0 else 0
                            
                            if is_green and vol_spike >= 1.5:
                                symbol_clean = stock.replace(".NS", "")
                                # TradingView URL format
                                tv_link = f"https://in.tradingview.com/chart/?symbol=NSE:{symbol_clean}"
                                
                                results.append({
                                    "Stock": symbol_clean,
                                    "Date": date.strftime("%d %b %Y"),
                                    "Volume Spike": f"{round(vol_spike, 1)}x",
                                    "Current Price": round(close_p, 2),
                                    "Open in TradingView": tv_link
                                })
                except Exception as e:
                    pass
            
            progress_bar.empty()

            if len(results) > 0:
                df = pd.DataFrame(results)
                
                # TradingView link ko clickable banane ke liye Streamlit column config
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
                st.info("Pichle 7 dino mein in stocks mein koi entry nahi mili.")
