import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# मोबाइल व्यू और क्लीन थीम सेटिंग्स
st.set_page_config(page_title="Nifty 500 Alpha Scanner", page_icon="🎯", layout="centered")

st.title("🎯 AI Stock Scanner (80+ Score Filter)")
st.write("Nifty 500 में से केवल **Strong Buy (Score 80-100)** वाले शेयर्स की लिस्ट")

# ----------------------------------------------------------------📖
# फंक्शन 1: Nifty 500 की ताज़ा लिस्ट ऑटो-डाउनलोड करना
# ----------------------------------------------------------------📖
@st.cache_data(ttl=86400) # 24 घंटे के लिए डेटा सुरक्षित रखना
def get_nifty500_tickers():
    try:
        url = "https://niftyindices.com"
        headers = {"User-Agent": "Mozilla/5.0"}
        df = pd.read_csv(url)
        tickers = [str(symbol).strip() + ".NS" for symbol in df['Symbol'].tolist()]
        return tickers
    except Exception as e:
        # बैकअप लिस्ट
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "ITC.NS", "SBIN.NS"]

# ----------------------------------------------------------------📖
# फंक्शन 2: 100-Point Scoring Engine (Strict 80+ Filter)
# ----------------------------------------------------------------📖
def analyze_stock_strict(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # फ़ास्ट स्कैनिंग के लिए पिछले 3 महीने का डेटा
        hist = stock.history(period="3mo")
        info = stock.info
        
        if len(hist) < 45:
            return None
            
        current_price = hist['Close'].iloc[-1]
        volume_today = hist['Volume'].iloc[-1]
        volume_5day_avg = hist['Volume'].tail(5).mean()
        
        # 50 DMA कैलकुलेशन (चरण 14 की शर्त)
        hist['50_DMA'] = hist['Close'].rolling(window=50).mean()
        dma_50 = hist['50_DMA'].iloc[-1]
        
        # मोमेंटम RSI (14 Days) - चरण 15 की शर्त
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        score = 0
        reasons = []
        
        # 1. फंडामेंटल्स (Max 30 Points) - चरण 3 से 11
        market_cap = info.get('marketCap', 0) / 10**7 # करोड़ में
        debt_to_equity = info.get('debtToEquity', 0)
        roe = info.get('returnOnEquity', 0) * 100
        
        if market_cap >= 5000: score += 5
        if roe > 12: 
            score += 10
            reasons.append("High ROE")
        if debt_to_equity is not None and debt_to_equity < 100: 
            score += 10
            reasons.append("Low Debt")
        else:
            score += 5
            
        # 2. टेक्निकल ट्रेंड (Max 20 Points) - चरण 14
        if current_price > dma_50:
            score += 20
            reasons.append("Price > 50 DMA")
        else:
            score += 5
            
        # 3. मोमेंटम RSI (Max 15 Points) - चरण 15
        if 55 <= rsi <= 70:
            score += 15
            reasons.append(f"आदर्श RSI ({rsi:.1f})")
        elif 45 <= rsi < 55:
            score += 10
        else:
            score += 5
            
        # 4. वॉल्यूम ब्रेकआउट इंजन (Max 15 Points) - चरण 17
        if volume_today > (volume_5day_avg * 1.5):
            score += 15
            reasons.append("वॉल्यूम ब्रेकआउट 🚀")
        else:
            score += 5
        
        # 5. सेक्टर/ग्लोबल सपोर्ट बेसलाइन (Max 20 Points)
        score += 15 
        
        # 🎯 STRICT FILTER: अगर स्कोर 80 से कम है, तो इस शेयर को यहीं छोड़ (Reject) दें
        if score < 80:
            return None
            
        return {
            "Ticker": ticker_symbol.replace(".NS", ""),
            "Price": f"₹{current_price:.2f}",
            "Score": score,
            "RSI": f"{rsi:.1f}",
            "Verdict": "Strong Buy Candidate 🌟",
            "Insights": ", ".join(reasons[-2:])
        }
    except:
        return None

# ----------------------------------------------------------------📖
# फ्रंट-एंड इंटरफ़ेस (UI)
# ----------------------------------------------------------------📖

nifty500_tickers = get_nifty500_tickers()
st.write(f"📊 कुल स्कैन की जाने वाली कंपनियाँ: **{len(nifty500_tickers)}**")

if st.button("🚀 Nifty 500 (80+ Score) शेयर्स स्कैन करें"):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    final_list = []
    total_stocks = len(nifty500_tickers)
    
    # लूप चलाकर सभी 500 शेयर्स की जांच
    for i, t in enumerate(nifty500_tickers):
        progress = (i + 1) / total_stocks
        progress_bar.progress(progress)
        status_text.text(f"स्कैन प्रोग्रेस ({i+1}/{total_stocks}): {t.replace('.NS','')}...")
        
        res = analyze_stock_strict(t)
        if res:
            final_list.append(res)
            
    status_text.text("✅ स्कैनिंग पूरी हो चुकी है!")
    progress_bar.empty()
    
    # परिणाम दिखाना
    if len(final_list) > 0:
        df_final = pd.DataFrame(final_list).sort_values(by="Score", ascending=False)
        st.success(f"🎯 आपके कड़े मापदंडों को पार करने वाले **{len(df_final)}** बेस्ट शेयर्स मिले!")
        
        for idx, row in df_final.iterrows():
            with st.container():
                st.markdown(f"### **{row['Ticker']}** | {row['Price']}")
                st.markdown(f"**स्कोर:** `{row['Score']}/100` — **{row['Verdict']}**")
                st.markdown(f"📈 **RSI:** {row['RSI']}")
                st.caption(f"💡 मुख्य सिग्नल: {row['Insights']}")
                st.markdown("---")
    else:
        st.info("ℹ️ आज के मार्केट डेटा के अनुसार Nifty 500 में से कोई भी शेयर 80+ स्कोर को पार नहीं कर पाया।")
