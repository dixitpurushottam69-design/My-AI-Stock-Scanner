import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# मोबाइल व्यू और क्लीन थीम सेटिंग्स
st.set_page_config(page_title="AI Alpha Scanner", page_icon="📈", layout="centered")

st.title("🎯 AI Stock Scanner (Cloud Optimized)")
st.write("100-Point Scoring System + Volume Breakout Engine")

# आपके पसंदीदा स्टॉक्स की लिस्ट (NSE के लिए .NS लगाना जरूरी है)
TICKERS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "ITC.NS", "SBIN.NS", "TATAMOTORS.NS"]

# ----------------------------------------------------------------📖
# क्लाउड-ऑप्टिमाइज्ड स्कोरिंग इंजन (NSE वेबसाइट पर निर्भरता खत्म)
# ----------------------------------------------------------------📖
def analyze_stock_cloud_safe(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # पिछले 3 महीने का डेली डेटा निकालना (वॉल्यूम और टेक्निकल्स के लिए पर्याप्त)
        hist = stock.history(period="3mo")
        info = stock.info
        
        if len(hist) < 50:
            return None
            
        # लाइव डेटा पॉइंट्स
        current_price = hist['Close'].iloc[-1]
        volume_today = hist['Volume'].iloc[-1]
        
        # पिछले 5 दिनों का एवरेज वॉल्यूम (आपके चरण 12 'Last 5 days volume' के लिए)
        volume_5day_avg = hist['Volume'].tail(5).mean()
        volume_total_avg = hist['Volume'].mean()
        
        # टेक्निकल्स (50 DMA कैलकुलेशन)
        # नोट: 200 DMA के लिए 1 साल का डेटा चाहिए होता है, लोडिंग फ़ास्ट रखने के लिए हम 50 DMA और ट्रेंड यूज़ कर रहे हैं
        hist['50_DMA'] = hist['Close'].rolling(window=50).mean()
        dma_50 = hist['50_DMA'].iloc[-1]
        
        # मोमेंटम (RSI 14 Days)
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        score = 0
        reasons = []
        
        # 1. फंडामेंटल्स (Max 30 Points) - Yahoo Finance से डायरेक्ट डेटा
        market_cap = info.get('marketCap', 0) / 10**7 # करोड़ में
        debt_to_equity = info.get('debtToEquity', 0)
        roe = info.get('returnOnEquity', 0) * 100
        
        if market_cap >= 5000: score += 5
        if roe > 12: 
            score += 10
            reasons.append("मजबूत रिटर्न (High ROE)")
        if debt_to_equity is not None and debt_to_equity < 100: 
            score += 10
            reasons.append("नियंत्रित कर्ज (Low Debt)")
        else:
            score += 5
            
        # 2. टेक्निकल ट्रेंड (Max 20 Points)
        if current_price > dma_50:
            score += 20
            reasons.append("बुलिश ट्रेंड (Price > 50 DMA)")
        else:
            score += 5
            
        # 3. मोमेंटम RSI (Max 15 Points) - चरण 15 की शर्त
        if 55 <= rsi <= 70:
            score += 15
            reasons.append(f"आदर्श मोमेंटम (RSI: {rsi:.1f})")
        elif 45 <= rsi < 55:
            score += 10
        else:
            score += 5
            
        # 4. वॉल्यूम और डिलीवरी ब्रेकआउट इंजन (Max 15 Points) - चरण 13 और 17
        # यदि आज का वॉल्यूम पिछले 5 दिनों के औसत से 1.5 गुना अधिक है
        if volume_today > (volume_5day_avg * 1.5):
            score += 15
            reasons.append("वॉल्यूम ब्रेकआउट (5-Day Avg से अधिक) 🔥")
        elif volume_today > volume_total_avg:
            score += 10
            reasons.append("बढ़ती हुई ट्रेडिंग वॉल्यूम")
        else:
            score += 5
        
        # 5. सेक्टर/ग्लोबल सपोर्ट बेसलाइन (Max 20 Points)
        score += 15 # डिफ़ॉल्ट सेफ मार्जिन
        
        # फाइनल निर्णय गाइडलाइंस (100-Point Scoring System)
        if score >= 80: verdict = "Strong Buy Candidate 🌟"
        elif 70 <= score < 79: verdict = "Watchlist / कन्फर्मेशन का इंतजार ⏳"
        else: verdict = "Weak / Avoid ❌"
        
        return {
            "Ticker": ticker_symbol.replace(".NS", ""),
            "Price": f"₹{current_price:.2f}",
            "Score": score,
            "RSI": f"{rsi:.1f}",
            "Volume Status": "Breakout 🚀" if volume_today > (volume_5day_avg * 1.5) else "Normal",
            "Verdict": verdict,
            "Top Insights": ", ".join(reasons[-2:]) # आखिरी दो सबसे बड़े कारण
        }
    except Exception as e:
        return None

# ----------------------------------------------------------------📖
# फ्रंट-एंड इंटरफ़ेस (UI) बटन ट्रिगर
# ----------------------------------------------------------------📖
if st.button("🚀 आज के शेयर्स स्कैन करें (Instant Engine)"):
    with st.spinner("लाइव क्लाउड सर्वर से डेटा प्रोसेस किया जा रहा है..."):
        final_list = []
        for t in TICKERS:
            res = analyze_stock_cloud_safe(t)
            if res:
                final_list.append(res)
                
        if len(final_list) > 0:
            # स्कोर के हिसाब से टॉप शेयर्स को सबसे ऊपर रखना
            df_final = pd.DataFrame(final_list).sort_values(by="Score", ascending=False)
            
            # मोबाइल-फ्रेंडली कार्ड लेआउट
            for idx, row in df_final.iterrows():
                with st.container():
                    st.markdown(f"### **{row['Ticker']}** | {row['Price']}")
                    st.markdown(f"**स्कोर:** `{row['Score']}/100` — **{row['Verdict']}**")
                    st.markdown(f"📈 **RSI:** {row['RSI']} | 📦 **वॉल्यूम स्थिति:** {row['Volume Status']}")
                    st.caption(f"💡 मुख्य सिग्नल: {row['Top Insights']}")
                    st.markdown("---")
        else:
            st.error("डेटा सिंक करने में समस्या हुई। कृपया कुछ समय बाद पुनः प्रयास करें।")
