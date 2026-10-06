import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# Custom RSI formula
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Website ki Setting
st.set_page_config(page_title="Smart Money Scanner", page_icon="🎯", layout="wide")
st.title("🎯 Brahmaastra Smart Money Scanner")

# Tab Layout Banaya (2 alag-alag features ke liye)
tab1, tab2 = st.tabs(["🚀 Auto Scanner (Support & Volume)", "🕵️‍♂️ Stock X-Ray (Specific Stock Check)"])

# ----------------- TAB 1: AUTO SCANNER -----------------
with tab1:
    st.markdown("**System Status:** Active & Ready to Scan Premium Setups...")
    
    stocks = [
        "RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "TCS.NS", 
        "NATIONALUM.NS", "TATAINVEST.NS", "SBIN.NS", "TATASTEEL.NS", "ITC.NS"
    ]
    
    if st.button("Scan Market Now 🚀"):
        with st.spinner("Scanning markets for Smart Money footprints... Please wait."):
            found_stocks = []
            
            for stock in stocks:
                try:
                    data = yf.download(stock, period="120d", progress=False)
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.get_level_values(0)
                        
                    if len(data) < 90:
                        continue
                        
                    data['90D_Low'] = data['Low'].rolling(window=90).min()
                    data['Avg_Vol_20'] = data['Volume'].rolling(window=20).mean()
                    data['RSI'] = compute_rsi(data['Close'], 14)
                    
                    latest = data.iloc[-1]
                    current_close = float(latest['Close'])
                    support_level = float(latest['90D_Low'])
                    current_vol = float(latest['Volume'])
                    avg_vol = float(latest['Avg_Vol_20'])
                    current_rsi = float(latest['RSI'])
                    
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
            
            if len(found_stocks) > 0:
                st.success("✅ Smart Money Footprints Found at Support!")
                st.dataframe(pd.DataFrame(found_stocks), use_container_width=True)
            else:
                st.warning("Koi stock aaj in 4 strict conditions ko pass nahi kar paya. Capital safe rakhein!")

# ----------------- TAB 2: STOCK X-RAY (NEW FEATURE) -----------------
with tab2:
    st.markdown("**Check if Smart Money bought your stock in the last 4 days:**")
    
    user_input = st.text_input("Stock ka naam likhein (e.g. RELIANCE.NS ya SBIN.NS)", "RELIANCE.NS")
    
    if st.button("Check History 🕵️‍♂️"):
        with st.spinner(f"Analyzing last 4 days data for {user_input}..."):
            try:
                # Agar user .NS lagana bhool jaye toh auto add karein
                stock_name = user_input.strip().upper()
                if not stock_name.endswith(".NS"):
                    stock_name += ".NS"
                    
                data = yf.download(stock_name, period="30d", progress=False)
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                    
                if len(data) >= 20:
                    data['Avg_Vol_20'] = data['Volume'].rolling(window=20).mean()
                    
                    # Pichle 4 din ka data uthayein
                    last_4_days = data.tail(4)
                    
                    smart_money_activity = []
                    
                    for date, row in last_4_days.iterrows():
                        open_p = float(row['Open'])
                        close_p = float(row['Close'])
                        vol = float(row['Volume'])
                        avg_vol = float(row['Avg_Vol_20'])
                        
                        # Logic: Green Candle (Close > Open) + High Volume (1.5x se zyada)
                        is_green_candle = close_p > open_p
                        vol_spike_ratio = vol / avg_vol if avg_vol > 0 else 0
                        
                        if is_green_candle and vol_spike_ratio >= 1.5:
                            smart_money_activity.append({
                                "Date": date.strftime("%d %b %Y"),
                                "Price Closed at (₹)": round(close_p, 2),
                                "Action": "Heavy Buying 🟢",
                                "Volume Spike": f"{round(vol_spike_ratio, 1)}x High"
                            })
                            
                    if len(smart_money_activity) > 0:
                        st.success(f"🔥 ALERT: {stock_name.replace('.NS', '')} mein pichle 4 dino mein Bade Khiladiyon ki ENTRY pakdi gayi hai!")
                        st.dataframe(pd.DataFrame(smart_money_activity), use_container_width=True)
                    else:
                        st.info(f"💤 {stock_name.replace('.NS', '')} mein pichle 4 dino mein koi achanak badi buying ya heavy volume spike nahi mila.")
                else:
                    st.error("Data nahi mila. Kripya stock ka sahi naam check karein.")
            except Exception as e:
                st.error("Kuch technical error aaya, kripya thodi der baad try karein.")
