import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import zipfile
import io
from datetime import datetime, timedelta

# मोबाइल व्यू और थीम सेटिंग्स
st.set_page_config(page_title="AI Alpha Scanner", page_icon="📈", layout="centered")

st.title("🎯 AI Stock Scanner (Bhavcopy Engine)")
st.write("Bhavcopy Delivery + 100-Point Scoring System")

# परीक्षण के लिए कुछ स्टॉक्स (वास्तविक ऐप में आप इसे बढ़ा सकते हैं)
TICKERS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "ITC.NS", "SBIN.NS"]

# ----------------------------------------------------------------📖
# फंक्शन 1: NSE से लेटेस्ट उपलब्ध Bhavcopy ऑटोमैटिक डाउनलोड करना (100% Free)
# ----------------------------------------------------------------📖
def download_nse_bhavcopy():
    # आज या पिछले कार्यदिवस (Working Day) की तारीख निकालना
    date_to_check = datetime.now()
    
    # यदि वीकेंड है तो शुक्रवार की तारीख सेट करना
    if date_to_check.weekday() == 5: # शनिवार
        date_to_check -= timedelta(days=1)
    elif date_to_check.weekday() == 6: # रविवार
        date_to_check -= timedelta(days=2)
        
    date_str = date_to_check.strftime("%Y%m%d")
    year = date_to_check.strftime("%Y")
    month_upper = date_to_check.strftime("%b").upper() # Ex: SEP, OCT
    
    # NSE की नई Bhavcopy URL संरचना (फुल रिपोर्ट जिसमें डिलीवरी % भी शामिल होता है)
    url = f"https://nseindia.com_{date_str}.csv"
    
    # ब्राउज़र जैसा दिखने के लिए Headers (ताकि NSE ब्लॉक न करे)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            # CSV को सीधे मैमोरी में लोड करना (बिना हार्ड डिस्क पर सेव किए - 100% सेफ और फास्ट)
            df_bhav = pd.read_csv(io.StringIO(response.text))
            # स्पेस हटाने के लिए कॉलम्स को ट्रिम करना
            df_bhav.columns = df_bhav.columns.str.strip()
            return df_bhav, date_to_check.strftime("%d-%b-%Y")
        else:
            # यदि आज की फाइल अभी अपलोड नहीं हुई है, तो एक दिन पीछे का प्रयास करें
            prev_date = date_to_check - timedelta(days=1)
            date_str = prev_date.strftime("%Y%m%d")
            url = f"https://nseindia.com_{date_str}.csv"
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                df_bhav = pd.read_csv(io.StringIO(response.text))
                df_bhav.columns = df_bhav.columns.str.strip()
                return df_bhav, prev_date.strftime("%d-%b-%Y")
    except Exception as e:
        st.warning(f"Bhavcopy कनेक्शन में समस्या आ रही है। केवल लाइव मार्केट डेटा का उपयोग होगा।")
        return None, None
    return None, None

# ----------------------------------------------------------------📖
# फंक्शन 2: 100-Point Scoring System + Bhavcopy Delivery Integration
# ----------------------------------------------------------------📖
def analyze_stock_advanced(ticker_symbol, df_bhav):
    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="1y")
        info = stock.info
        
        if len(hist) < 200:
            return None
            
        current_price = hist['Close'].iloc[-1]
        volume_today = hist['Volume'].iloc[-1]
        volume_avg = hist['Volume'].mean()
        
        # टेक्निकल्स (DMA)
        hist['50_DMA'] = hist['Close'].rolling(window=50).mean()
        hist['200_DMA'] = hist['Close'].rolling(window=200).mean()
        dma_50 = hist['50_DMA'].iloc[-1]
        dma_200 = hist['200_DMA'].iloc[-1]
        
        # मोमेंटम (RSI)
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        score = 0
        reasons = []
        
        # 1. फंडामेंटल्स (Max 30 Points)
        market_cap = info.get('marketCap', 0) / 10**7
        debt_to_equity = info.get('debtToEquity', 0)
        roe = info.get('returnOnEquity', 0) * 100
        
        if market_cap >= 5000: score += 5
        if roe > 15: 
            score += 10
            reasons.append("उच्च ROE (>15%)")
        if debt_to_equity < 100: 
            score += 10
            reasons.append("कम/नियंत्रित कर्ज")
        else:
            score += 5
            
        # 2. टेक्निकल ट्रेंड (Max 20 Points)
        if current_price > dma_50 and dma_50 > dma_200:
            score += 20
            reasons.append("मजबूत अपट्रेंड (Price > 50 > 200 DMA)")
        elif current_price > dma_200:
            score += 10
            
        # 3. मोमेंटम RSI (Max 15 Points)
        if 55 <= rsi <= 70:
            score += 15
            reasons.append(f"आदर्श RSI मोमेंटम ({rsi:.1f})")
            
        # 4. ADVANCED BHAVCOPY DELIVERY DATA ANALYSIS (Max 15 Points)
        nse_symbol = ticker_symbol.replace(".NS", "")
        delivery_pct = 0
        
        if df_bhav is not None:
            # Bhavcopy में से इस विशेष स्टॉक की रो (Row) खोजना
            stock_row = df_bhav[df_bhav['SYMBOL'] == nse_symbol]
            if not stock_row.empty:
                # DELIV_QTY और DELIV_PER (डिलीवरी प्रतिशत कॉलम)
                delivery_pct = float(stock_row['DELIV_PER'].values[0])
                
                # यदि डिलीवरी 45% से अधिक है, तो इसका मतलब है कि बड़ी संस्थाएं (FIIs/DIIs) माल जमा कर रही हैं
                if delivery_pct >= 45.0:
                    score += 15
                    reasons.append(f"हाई डिलीवरी ब्रेकआउट ({delivery_pct}%) 🔥")
                elif 30.0 <= delivery_pct < 45.0:
                    score += 10
                    reasons.append(f"स्थिर डिलीवरी ({delivery_pct}%)")
                else:
                    score += 5
        else:
            # यदि किसी वजह से Bhavcopy नहीं मिलती, तो सामान्य वॉल्यूम का सहारा लें
            if volume_today > (volume_avg * 1.5):
                score += 10
                reasons.append("वॉल्यूम स्पाइक")
        
        # 5. सेक्टर/ग्लोबल फैक्टर्स बेसलाइन (Max 20 Points)
        score += 10
        
        # फाइनल निर्णय ग्रेडिंग
        if score >= 80: verdict = "Strong Buy Candidate 🌟"
        elif 70 <= score < 79: verdict = "Watchlist / कन्फर्मेशन का इंतजार ⏳"
        else: verdict = "Weak / Avoid ❌"
        
        return {
            "Ticker": nse_symbol,
            "Price": f"₹{current_price:.2f}",
            "Score": score,
            "RSI": f"{rsi:.1f}",
            "Delivery %": f"{delivery_pct}%" if delivery_pct > 0 else "N/A",
            "Verdict": verdict,
            "Top Reason": ", ".join(reasons[-2:]) # आखिरी दो सबसे मजबूत कारण दिखाएं
        }
    except:
        return None

# ----------------------------------------------------------------📖
# फ्रंट-एंड इंटरफ़ेस (UI) बटन ट्रिगर
# ----------------------------------------------------------------📖
if st.button("🚀 आज के शेयर्स स्कैन करें (Bhavcopy Engine)"):
    with st.spinner("1. NSE से ताज़ा Bhavcopy डाउनलोड की जा रही है..."):
        df_bhav, data_date = download_nse_bhavcopy()
        
        if data_date:
            st.success(f"✅ सफल! डेटा दिनांक: {data_date} की Bhavcopy एक्टिवेटेड।")
        else:
            st.info("ℹ️ लाइव या बैकअप डेटा सिंक का उपयोग किया जा रहा है।")
            
    with st.spinner("2. आपके 100-Point मापदंडों के अनुसार शेयर्स प्रोसेस हो रहे हैं..."):
        final_list = []
        for t in TICKERS:
            res = analyze_stock_advanced(t, df_bhav)
            if res:
                final_list.append(res)
                
        # डेटा को टेबल और कार्ड फॉर्मेट में बदलना
        df_final = pd.DataFrame(final_list).sort_values(by="Score", ascending=False)
        
        # मोबाइल कार्ड लेआउट में डिस्प्ले करना
        for idx, row in df_final.iterrows():
            with st.container():
                st.markdown(f"### **{row['Ticker']}** | {row['Price']}")
                st.markdown(f"**स्कोर:** `{row['Score']}/100` — **{row['Verdict']}**")
                st.markdown(f"📈 **RSI:** {row['RSI']} | 📦 **डिलिवरी प्रतिशत:** {row['Delivery %']}")
                st.caption(f"💡 AI सिग्नल: {row['Top Reason']}")
                st.markdown("---")
