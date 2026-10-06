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

# Website ki Setting
st.set_page_config(page_title="Smart Money", page_icon="🎯", layout="wide")
st.title("🎯 Smart Money (Stealth Accumulation) Scanner")
st.markdown("**Logic:** RSI < 40 + Stealth Buying / Absorption near Support")

if st.button("Run Scan 🚀"):
    file_path = "Trading_Symbols_Chartink.txt"
    stocks = []
    
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            stocks = [line.strip() + ".NS" for line in f.readlines() if line.strip()]
    else:
        st.error("Trading_Symbols_Chartink.txt file nahi mili. Kripya GitHub par check karein.")

    if stocks:
        with st.spinner("Scanning 592 stocks for RSI < 40 & Stealth Accumulation..."):
            results = []
            progress_bar = st.progress(0)
            
            for i, stock in enumerate(stocks):
                progress_bar.progress((i + 1) / len(stocks))
                
                try:
                    # 120 din ka data chahiye taki RSI aur Average Volume sahi aaye
                    data = yf.download(stock, period="120d", progress=False)
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.get_level_values(0)
                        
                    if len(data) >= 90:
                        data['RSI'] = compute_rsi(data['Close'], 14)
                        latest_rsi = float(data['RSI'].iloc[-1])
                        
                        # Filter 1: Sirf woh stocks jo oversold (RSI < 40) zone mein ja rahe hain
                        if latest_rsi <= 40:
                            data['Avg_Vol_20'] = data['Volume'].rolling(window=20).mean()
                            last_7_days = data.tail(7)
                            
                            accumulation_found = False
                            
                            # Filter 2: Stealth Accumulation Check karna
                            for date, row in last_7_days.iterrows():
                                open_p = float(row['Open'])
                                close_p = float(row['Close'])
                                high_p = float(row['High'])
                                low_p = float(row['Low'])
                                
                                body = abs(open_p - close_p)
                                lower_wick = min(open_p, close_p)
