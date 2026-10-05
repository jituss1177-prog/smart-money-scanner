import yfinance as yf
import pandas as pd
import pandas_ta as ta

# Aap yahan aur bhi stocks add kar sakte hain (Last mein .NS lagana zaroori hai)
stocks = [
    "RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "TCS.NS", 
    "NATIONALUM.NS", "TATAINVEST.NS", "SBIN.NS", "TATASTEEL.NS", "ITC.NS"
]

print(f"Scanning {len(stocks)} stocks for Smart Money footprints...\n")

found_stocks = []

for stock in stocks:
    try:
        # Pichle 120 din ka data download karein taaki 90-day support nikal sake
        data = yf.download(stock, period="120d", progress=False)
        
        if len(data) < 90:
            continue
            
        # 90-Day Low (Support) calculate karein
        data['90D_Low'] = data['Low'].rolling(window=90).min()
        
        # 20-Day Average Volume calculate karein
        data['Avg_Vol_20'] = data['Volume'].rolling(window=20).mean()
        
        # RSI (14) calculate karein
        data['RSI'] = ta.rsi(data['Close'], length=14)
        
        # Latest (kal ka) closed data uthayein
        latest = data.iloc[-1]
        
        current_close = latest['Close']
        support_level = latest['90D_Low']
        current_vol = latest['Volume']
        avg_vol = latest['Avg_Vol_20']
        current_rsi = latest['RSI']
        
        # CONDITIONS (Aapke rules ke hisaab se)
        # 1. Price 90-Day support ke 3% ke andar ho (Near Support)
        is_near_support = current_close <= (support_level * 1.03)
        
        # 2. Volume average se kam se kam 2.5x (250%) zyada ho (Smart Money Entry)
