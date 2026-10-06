import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# Custom RSI formula (Hidden Logic)
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Website ki Setting - Minimal
st.set_page_config(page_title="smart m", layout="wide")
st.title("smart m")

# Tabs ke naam simple kar diye gaye
tab1, tab2 = st.tabs(["List 1", "List 2"])

# ----------------- TAB 1: AUTO SCANNER (Stealth) -----------------
with tab1:
    stocks = [
        "RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "TCS.NS", 
        "NATIONALUM.NS", "TATAINVEST.NS", "SBIN.NS", "TATASTEEL.NS", "ITC.NS"
    ]
    
    if st.button("Run"):
        with st.spinner("..."):
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
                            "Sym": stock.replace(".NS", ""),
                            "P": round(current_close, 2),
                            "S": round(support_level, 2),
                            "R": round(current_rsi, 2),
                            "V": f"{round(current_vol / avg_vol, 1)}x"
                        })
                except Exception as e:
                    pass
            
            if len(found_stocks) > 0:
                st.dataframe(pd.DataFrame(found_stocks), use_container_width=True)
            else:
                st.write("0")

# ----------------- TAB 2: SPECIFIC CHECK (Stealth) -----------------
with tab2:
    # Koi bhi text ya hint nahi, sirf khali box
    user_input = st.text_input("", "")
    
    if st.button("Check"):
        if user_input.strip() == "":
            st.warning("!")
        else:
            with st.spinner("..."):
                try:
                    stock_name = user_input.strip().upper()
                    if not stock_name.endswith(".NS"):
                        stock_name += ".NS"
                        
                    data = yf.download(stock_name, period="30d", progress=False)
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.get_level_values(0)
                        
                    if len(data) >= 20:
                        data['Avg_Vol_20'] = data['Volume'].rolling(window=20).mean()
                        
                        last_7_days = data.tail(7)
                        
                        smart_money_activity = []
                        
                        for date, row in last_7_days.iterrows():
                            open_p = float(row['Open'])
                            close_p = float(row['Close'])
                            vol = float(row['Volume'])
                            avg_vol = float(row['Avg_Vol_20'])
                            
                            is_green_candle = close_p > open_p
                            vol_spike_ratio = vol / avg_vol if avg_vol > 0 else 0
                            
                            if is_green_candle and vol_spike_ratio >= 1.5:
                                smart_money_activity.append({
                                    "D": date.strftime("%d %b"),
                                    "P": round(close_p, 2),
                                    "A": "B",
                                    "V": f"{round(vol_spike_ratio, 1)}x"
                                })
                                
                        if len(smart_money_activity) > 0:
                            st.success("✅")
                            st.dataframe(pd.DataFrame(smart_money_activity), use_container_width=True)
                        else:
                            st.info("0")
                    else:
                        st.error("X")
                except Exception as e:
                    st.error("X")
