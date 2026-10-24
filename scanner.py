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

# Helper function: Low-Volume Sell-Off & 1R Strategy Logic
def analyze_low_vol_strategy(data, risk_1r=11878.0):
    if len(data) < 25:
        return None

    df = data.copy()
    df['Avg_Vol_20'] = df['Volume'].rolling(window=20).mean()
    df['Pct_Change'] = df['Close'].pct_change() * 100.0
    
    # 5-Bar Tight Channel (Parallel Lines)
    df['Channel_High'] = df['High'].rolling(window=5).max()
    df['Channel_Low'] = df['Low'].rolling(window=5).min()
    df['Channel_Width'] = ((df['Channel_High'] - df['Channel_Low']) / df['Close']) * 100.0

    # Step 1: High-Volume Momentum Burst in last 12 bars (Circle 1)
    # Volume > 2x Avg AND Green Candle with > 2.5% move
    df['Bull_Burst'] = (df['Volume'] > df['Avg_Vol_20'] * 2.0) & (df['Close'] > df['Open']) & (df['Pct_Change'] > 2.5)
    
    # Check if a burst happened between 2 and 12 bars ago
    recent_burst_window = df['Bull_Burst'].iloc[-13:-1]
    has_recent_burst = bool(recent_burst_window.any())
    
    if not has_recent_burst:
        return None

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    close_p = float(latest['Close'])
    open_p = float(latest['Open'])
    vol = float(latest['Volume'])
    avg_vol = float(latest['Avg_Vol_20'])
    
    if avg_vol <= 0:
        return None

    vol_ratio = vol / avg_vol
    highest_12 = float(df['High'].iloc[-13:].max())
    lowest_12 = float(df['Low'].iloc[-13:].min())
    
    # Step 2: Low-Volume Sell-Off / Pullback in Tight Range (Advance Radar)
    in_pullback = (close_p < highest_12) and (close_p > lowest_12)
    is_low_vol = vol_ratio <= 0.70  # Volume dried up (< 70% of 20 SMA)
    
    # Current 5-day channel or previous 5-day channel width
    curr_width = float(latest['Channel_Width'])
    prev_width = float(prev['Channel_Width'])
    
    # Condition A: ADVANCE RADAR (Breakout se pehle - Low-Volume Sell-off + Tight Base)
    is_radar = has_recent_burst and in_pullback and is_low_vol and (curr_width <= 5.5)
    
    # Condition B: BREAKOUT TRIGGER (Tight base ke baad Volume Spike ke saath Breakout)
    # Previous bar was in a tight range & low volume occurred recently, today broke prev Channel High
    had_low_vol_recently = bool((df['Volume'].iloc[-6:-1] < df['Avg_Vol_20'].iloc[-6:-1] * 0.75).any())
    prev_channel_high = float(prev['Channel_High'])
    prev_channel_low = float(prev['Channel_Low'])
    
    is_breakout = (
        has_recent_burst 
        and had_low_vol_recently 
        and (prev_width <= 6.0) 
        and (close_p > prev_channel_high) 
        and (close_p > open_p) 
        and (vol_ratio >= 1.2)
    )

    if not (is_radar or is_breakout):
        return None

    # 1R Position Sizing Calculation
    sl_price = prev_channel_low if is_breakout else float(latest['Channel_Low'])
    trigger_price = prev_channel_high if is_breakout else float(latest['Channel_High'])
    
    # Minimum 0.5% Stop-Loss distance safeguard
    risk_per_share = max(close_p - sl_price, close_p * 0.005)
    base_qty = int(round(risk_1r / risk_per_share))
    tracker_qty = base_qty + 1  # +1 Tracker share (1001 / 2002 pattern)
    capital_req = tracker_qty * close_p
    target_3r = close_p + (risk_per_share * 3.0)

    status = "🟢 BREAKOUT BUY 🚀" if is_breakout else "🟡 RADAR (Low-Vol Pullback)"

    return {
        "Status": status,
        "Current Price": round(close_p, 2),
        "Breakout Trigger": round(trigger_price, 2),
        "Stop-Loss (SL)": round(sl_price, 2),
        "Vol Ratio": f"{round(vol_ratio, 2)}x",
        "Buy Qty (+1 Tracker)": tracker_qty,
        "Capital Req (₹)": round(capital_req, 0),
        "Target (3R)": round(target_3r, 2)
    }

# Website ki Setting (Poori tarah se Stealth)
st.set_page_config(page_title="Smart Money", page_icon="🎯", layout="wide")
st.title("🎯 Smart Money")

# 3 Tabs create kiye (Tab 3 = New Low-Volume Sell-Off & 1R Strategy)
tab1, tab2, tab3 = st.tabs([
    "List Scan (RSI < 35)", 
    "Manual Check", 
    "🔥 Low-Vol 1R Strategy (Advance Radar)"
])

# ---------------- TAB 1: AUTO SCANNER (Last 5 Days) ----------------
with tab1:
    if st.button("Run Scan 🚀", key="btn_tab1"):
        file_path = "Trading_Symbols_Chartink.txt"
        stocks = []
        
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                stocks = [line.strip() + ".NS" for line in f.readlines() if line.strip()]
        else:
            st.error("Trading_Symbols_Chartink.txt file nahi mili.")

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
                            prev_rsi = float(data['RSI'].iloc[-2])
                            
                            # Filter 1: Kal RSI 35 ke upar tha, aur aaj 35 ya usse niche aaya hai (Fresh Cross)
                            if prev_rsi > 35 and latest_rsi <= 35:
                                data['Avg_Vol_20'] = data['Volume'].rolling(window=20).mean()
                                
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
                    except Exception:
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
                    st.info("Koi fresh RSI < 35 breakdown aur recent accumulation nahi mili.")

# ---------------- TAB 2: MANUAL CHECK (Last 5 Days + 1R Check) ----------------
with tab2:
    user_input = st.text_input("Stock Name (e.g. INFY, HDFCBANK)", "")
    
    if st.button("Check Stock 🕵️‍♂️", key="btn_tab2"):
        if user_input.strip() == "":
            st.warning("Pehle kisi stock ka naam likhein.")
        else:
            with st.spinner("Analyzing recent activity..."):
                try:
                    stock_name = user_input.strip().upper()
                    if not stock_name.endswith(".NS"):
                        stock_name += ".NS"
                        
                    data = yf.download(stock_name, period="60d", progress=False)
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.get_level_values(0)
                        
                    if len(data) >= 25:
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
                            elif not is_green and vol_spike <= 0.65:
                                setup = "Low-Volume Sell-Off (Weak Drop) 🟡"
                                
                            if setup != "":
                                activity.append({
                                    "Date": date.strftime("%d %b %Y"),
                                    "Setup Type": setup,
                                    "Closing Price": round(close_p, 2),
                                    "Volume Spike": f"{round(vol_spike, 2)}x"
                                })
                                
                        if len(activity) > 0:
                            st.success(f"Activity Found for {stock_name.replace('.NS', '')}")
                            st.dataframe(pd.DataFrame(activity), use_container_width=True, hide_index=True)
                        else:
                            st.info("Pichle 5 dino mein koi special activity nahi mili.")
                            
                        # Show 1R Strategy Status for this stock as well
                        strat_res = analyze_low_vol_strategy(data)
                        if strat_res:
                            st.subheader("🎯 Low-Vol 1R Strategy Match!")
                            st.json(strat_res)
                    else:
                        st.error("Data nahi mila. Sahi naam type karein.")
                except Exception:
                    st.error("Kuch technical error aaya. Sahi naam check karein.")

# ---------------- TAB 3: LOW-VOLUME SELL-OFF & 1R STRATEGY ----------------
with tab3:
    st.markdown("### 🎯 Low-Volume Sell-Off & Tight Base Scanner (1R System)")
    st.caption(
        "Yeh scanner pehle High-Volume Momentum Burst dhoondhta hai, aur phir un stocks ko filter karta hai "
        "jo Low-Volume Sell-Off (pullback) ya Tight Breakout zone mein hain."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        risk_1r_input = st.number_input("Fixed Risk Per Trade (1R in ₹)", value=11878.0, step=500.0)
    with col2:
        timeframe_choice = st.selectbox("Select Timeframe", ["1d (Daily Chart)", "1h (Hourly Chart)"])
        
    if st.button("Scan Low-Vol Strategy 🔥", key="btn_tab3"):
        file_path = "Trading_Symbols_Chartink.txt"
        stocks = []
        
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                stocks = [line.strip() + ".NS" for line in f.readlines() if line.strip()]
        else:
            st.error("Trading_Symbols_Chartink.txt file nahi mili.")

        if stocks:
            with st.spinner("Scanning stocks for High-Vol Burst + Low-Vol Sell-Off..."):
                strat_results = []
                progress_bar = st.progress(0)
                
                is_hourly = timeframe_choice.startswith("1h")
                dl_period = "30d" if is_hourly else "60d"
                dl_interval = "1h" if is_hourly else "1d"
                
                for i, stock in enumerate(stocks):
                    progress_bar.progress((i + 1) / len(stocks))
                    
                    try:
                        data = yf.download(stock, period=dl_period, interval=dl_interval, progress=False)
                        if isinstance(data.columns, pd.MultiIndex):
                            data.columns = data.columns.get_level_values(0)
                            
                        res = analyze_low_vol_strategy(data, risk_1r=risk_1r_input)
                        if res is not None:
                            symbol_clean = stock.replace(".NS", "")
                            tv_link = f"https://in.tradingview.com/chart/?symbol=NSE:{symbol_clean}"
                            
                            strat_results.append({
                                "Stock": symbol_clean,
                                "Status": res["Status"],
                                "Current Price": res["Current Price"],
                                "Breakout Trigger": res["Breakout Trigger"],
                                "Stop-Loss (SL)": res["Stop-Loss (SL)"],
                                "Vol Ratio": res["Vol Ratio"],
                                "Buy Qty (+1 Tracker)": res["Buy Qty (+1 Tracker)"],
                                "Capital Req (₹)": res["Capital Req (₹)"],
                                "Target (3R)": res["Target (3R)"],
                                "Open in TradingView": tv_link
                            })
                    except Exception:
                        pass
                        
                progress_bar.empty()
                
                if len(strat_results) > 0:
                    df_strat = pd.DataFrame(strat_results)
                    # Sort so BREAKOUT BUY comes on top, followed by RADAR
                    df_strat = df_strat.sort_values(by="Status", ascending=True)
                    
                    st.success(f"Total {len(strat_results)} stocks mile jo setup mein hain!")
                    st.dataframe(
                        df_strat,
                        column_config={
                            "Open in TradingView": st.column_config.LinkColumn(
                                "Open in TradingView", display_text="View Chart 📈"
                            )
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Abhi list mein koi stock Low-Volume Sell-Off ya Tight Breakout zone mein nahi mila.")
