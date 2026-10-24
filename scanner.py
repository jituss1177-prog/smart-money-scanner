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

# 2 Tabs create kiye (Original Structure)
tab1, tab2 = st.tabs(["List Scan", "Manual Check"])

# ---------------- TAB 1: AUTO SCANNER (Old + Latest Strategy in Separate Column) ----------------
with tab1:
    if st.button("Run Scan 🚀"):
        file_path = "Trading_Symbols_Chartink.txt"
        stocks = []
        
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                stocks = [line.strip() + ".NS" for line in f.readlines() if line.strip()]
        else:
            st.error("Trading_Symbols_Chartink.txt file nahi mili.")

        if stocks:
            with st.spinner("Processing list... please wait."):
                results = []              # Old Strategy List
                latest_strat_results = [] # New Strategy List (Alag Column ke liye)
                progress_bar = st.progress(0)
                
                for i, stock in enumerate(stocks):
                    progress_bar.progress((i + 1) / len(stocks))
                    
                    try:
                        data = yf.download(stock, period="120d", progress=False)
                        if isinstance(data.columns, pd.MultiIndex):
                            data.columns = data.columns.get_level_values(0)
                            
                        if len(data) >= 90:
                            data['RSI'] = compute_rsi(data['Close'], 14)
                            data['Avg_Vol_20'] = data['Volume'].rolling(window=20).mean()
                            
                            symbol_clean = stock.replace(".NS", "")
                            tv_link = f"https://in.tradingview.com/chart/?symbol=NSE:{symbol_clean}"
                            current_close = float(data['Close'].iloc[-1])
                            
                            # ==========================================================
                            # 1. OLD STRATEGY (Bilkul Original Logic - Untouched)
                            # ==========================================================
                            latest_rsi = float(data['RSI'].iloc[-1])
                            prev_rsi = float(data['RSI'].iloc[-2])
                            
                            # Filter 1: Kal RSI 35 ke upar tha, aur aaj 35 ya usse niche aaya hai (Fresh Cross)
                            if prev_rsi > 35 and latest_rsi <= 35:
                                last_5_days = data.tail(5)
                                accumulation_found = False
                                entry_date = ""
                                
                                # Filter 2: Stealth Accumulation (Absorption) in Last 5 Days
                                for date, row in last_5_days.iterrows():
                                    open_p = float(row['Open'])
                                    close_p = float(row['Close'])
                                    high_p = float(row['High'])
                                    low_p = float(row['Low'])
                                    
                                    body = abs(open_p - close_p)
                                    lower_wick = min(open_p, close_p) - low_p
                                    total_range = high_p - low_p
                                    
                                    # Absorption Logic
                                    if total_range > 0 and lower_wick > body and (lower_wick / total_range) >= 0.4:
                                        accumulation_found = True
                                        entry_date = date.strftime("%d %b %Y")
                                        break
                                
                                if accumulation_found:
                                    results.append({
                                        "Stock": symbol_clean,
                                        "Entry Date": entry_date,
                                        "Current Price": round(current_close, 2),
                                        "RSI": round(latest_rsi, 2),
                                        "Open in TradingView": tv_link
                                    })

                            # ==========================================================
                            # 2. LATEST STRATEGY (High-Vol Burst + Low-Vol Sell-Off Entry)
                            # ==========================================================
                            data['Pct_Change'] = data['Close'].pct_change() * 100.0
                            data['Channel_High'] = data['High'].rolling(window=5).max()
                            data['Channel_Low'] = data['Low'].rolling(window=5).min()
                            data['Channel_Width'] = ((data['Channel_High'] - data['Channel_Low']) / data['Close']) * 100.0
                            
                            # Step 1: Recent High-Volume Momentum Burst (Pichle 15 din mein bada volume move)
                            data['Bull_Burst'] = (
                                (data['Volume'] > data['Avg_Vol_20'] * 1.8) & 
                                (data['Close'] > data['Open']) & 
                                (data['Pct_Change'] > 2.5)
                            )
                            has_recent_burst = bool(data['Bull_Burst'].iloc[-15:-1].any())
                            
                            # Step 2: Low-Volume Sell-Off in recent days (Girawat mein volume sookhna)
                            data['Low_Vol_Drop'] = (
                                (data['Close'] < data['Open']) & 
                                (data['Volume'] < data['Avg_Vol_20'] * 0.75)
                            )
                            has_low_vol_selloff = bool(data['Low_Vol_Drop'].iloc[-8:-1].any())
                            
                            # Step 3: Entry Trigger in Last 3 Days (Tight Base Breakout ya Reversal Entry)
                            if has_recent_burst and has_low_vol_selloff:
                                recent_3 = data.tail(3)
                                strat_entry_found = False
                                strat_entry_date = ""
                                strat_signal = ""
                                
                                for idx in range(-3, 0):
                                    row = data.iloc[idx]
                                    prev_row = data.iloc[idx - 1]
                                    
                                    c_close = float(row['Close'])
                                    c_open = float(row['Open'])
                                    c_vol = float(row['Volume'])
                                    c_avg_vol = float(row['Avg_Vol_20'])
                                    prev_ch_high = float(prev_row['Channel_High'])
                                    prev_width = float(prev_row['Channel_Width'])
                                    
                                    # Entry 1: Tight Channel Breakout with Volume
                                    if c_close > prev_ch_high and c_close > c_open and c_vol >= (c_avg_vol * 1.1) and prev_width <= 6.5:
                                        strat_entry_found = True
                                        strat_entry_date = data.index[idx].strftime("%d %b %Y")
                                        strat_signal = "Breakout Entry 🚀"
                                    # Entry 2: Low-Volume Pullback Reversal (TightSL Entry)
                                    elif c_close > c_open and c_close > float(prev_row['High']) and float(prev_row['Volume']) < (c_avg_vol * 0.70):
                                        strat_entry_found = True
                                        strat_entry_date = data.index[idx].strftime("%d %b %Y")
                                        strat_signal = "Pullback Entry 🎯"
                                
                                if strat_entry_found:
                                    latest_strat_results.append({
                                        "Stock": symbol_clean,
                                        "Entry Date": strat_entry_date,
                                        "Current Price": round(current_close, 2),
                                        "Signal": strat_signal,
                                        "Open in TradingView": tv_link
                                    })

                    except Exception as e:
                        pass
                
                progress_bar.empty()

                # Screen par 2 Alag Columns: Left = Old Strategy, Right = Latest Strategy
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("📌 Old Strategy (RSI < 35)")
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
                        st.info("Koi fresh RSI < 35 breakdown aur recent accumulation nahi mili.")

                with col2:
                    st.subheader("🔥 Latest Strategy (Low-Vol Entry)")
                    if len(latest_strat_results) > 0:
                        df_new = pd.DataFrame(latest_strat_results)
                        st.dataframe(
                            df_new,
                            column_config={
                                "Open in TradingView": st.column_config.LinkColumn(
                                    "Open in TradingView", display_text="View Chart 📈"
                                )
                            },
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("Abhi latest strategy mein koi fresh entry nahi mili.")

# ---------------- TAB 2: MANUAL CHECK (Last 5 Days - Bilkul Original) ----------------
with tab2:
    user_input = st.text_input("Stock Name (e.g. INFY, HDFCBANK)", "")
    
    if st.button("Check Stock 🕵️‍♂️"):
        if user_input.strip() == "":
            st.warning("Pehle kisi stock ka naam likhein.")
        else:
            with st.spinner("Analyzing recent activity..."):
                try:
                    stock_name = user_input.strip().upper()
                    if not stock_name.endswith(".NS"):
                        stock_name += ".NS"
                        
                    data = yf.download(stock_name, period="30d", progress=False)
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.get_level_values(0)
                        
                    if len(data) >= 20:
                        data['Avg_Vol_20'] = data['Volume'].rolling(window=20).mean()
                        
                        last_5_days = data.tail(5)
                        activity = []
                        
                        for date, row in last_5_days.iterrows():
                            open_p = float(row['Open'])
                            close_p = float(row['Close'])
                            high_p = float(row['High'])
                            low_p = float(row['Low'])
                            vol = float(row['Volume'])
                            avg_vol = float(row['Avg_Vol_20'])
                            
                            body = abs(open_p - close_p)
                            lower_wick = min(open_p, close_p) - low_p
                            total_range = high_p - low_p
                            vol_spike = vol / avg_vol if avg_vol > 0 else 0
                            is_green = close_p > open_p
                            
                            setup = ""
                            
                            if total_range > 0 and lower_wick > body and (lower_wick / total_range) >= 0.4:
                                setup = "Absorption (Stealth) 🟢"
                            elif is_green and vol_spike >= 1.5:
                                setup = "Aggressive Buy 🚀"
                                
                            if setup != "":
                                activity.append({
                                    "Date": date.strftime("%d %b %Y"),
                                    "Setup Type": setup,
                                    "Closing Price": round(close_p, 2),
                                    "Volume Spike": f"{round(vol_spike, 1)}x"
                                })
                                
                        if len(activity) > 0:
                            st.success(f"Activity Found for {stock_name.replace('.NS', '')}")
                            st.dataframe(pd.DataFrame(activity), use_container_width=True, hide_index=True)
                        else:
                            st.info("Pichle 5 dino mein koi special activity nahi mili.")
                    else:
                        st.error("Data nahi mila. Sahi naam type karein.")
                except Exception as e:
                    st.error("Kuch technical error aaya. Sahi naam check karein.")
