import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# Website ki setting
st.set_page_config(page_title="Smart Money Scanner", page_icon="🎯", layout="wide")

st.title("🎯 Smart Money (90D Support) Scanner")
st.markdown("**System Status:** Active & Ready to Scan...")

stocks = [
    "RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "TCS.NS", 
    "NATIONALUM.NS", "TATAINVEST.NS", "SBIN.NS", "TATASTEEL.NS", "ITC.NS"
]

# Button dabane par yeh chalega
if st.button("Scan Now 🚀"):
    with st.spinner("Scanning markets for Smart Money footprints... Please wait."):
        found_stocks = []
        
        for stock in stocks:
            try:
                data = yf.download(stock, period="120d", progress=False)
                if len(data) < 90:
                    continue
                    
                data['90D_Low'] = data['Low'].rolling(window=90).min()
                data['Avg_Vol_20'] = data['Volume'].rolling(window=20).mean()
                data['RSI'] = ta.rsi(data['Close'], length=14)
                
                latest = data.iloc[-1]
                
                current_close = float(latest['Close'].iloc[0]) if isinstance(latest['Close'], pd.Series) else float(latest['Close'])
                support_level = float(latest['90D_Low'].iloc[0]) if isinstance(latest['90D_Low'], pd.Series) else float(latest['90D_Low'])
                current_vol = float(latest['Volume'].iloc[0]) if isinstance(latest['Volume'], pd.Series) else float(latest['Volume'])
                avg_vol = float(latest['Avg_Vol_20'].iloc[0]) if isinstance(latest['Avg_Vol_20'], pd.Series) else float(latest['Avg_Vol_20'])
                current_rsi = float(latest['RSI'].iloc[0]) if isinstance(latest['RSI'], pd.Series) else float(latest['RSI'])
                
                is_near_support = current_close <= (support_level * 1.03)
                is_high_volume = current_vol >= (avg_vol * 2.5)
                is_rsi_oversold = current_rsi <= 40
                
                if is_near_support and is_high_volume and is_rsi_oversold:
                    found_stocks.append({
                        "Stock": stock.replace(".NS", ""),
                        "Price (₹)": round(current_close, 2),
                        "Support (₹)": round(support_level, 2),
                        "RSI": round(current_rsi, 2),
                        "Volume Spike": f"{round(current_vol / avg_vol, 1)}x"
                    })
            except Exception as e:
                pass
        
        # Result Screen par dikhana
        if len(found_stocks) > 0:
            st.success("✅ Smart Money Footprints Found!")
            df = pd.DataFrame(found_stocks)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("Koi stock aaj in 4 strict conditions ko pass nahi kar paya. Capital safe rakhein!")
