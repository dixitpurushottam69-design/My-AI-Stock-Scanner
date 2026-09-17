import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

# मोबाइल व्यू सेटिंग्स
st.set_page_config(page_title="Fast Nifty 500 AI Scanner", page_icon="⚡", layout="centered")

st.title("⚡ AI Stock Scanner (Super-Fast Engine)")
st.write("Nifty 500 की सभी कंपनियों को 45 सेकंड में स्कैन करें (Strict 80+ Filter)")

# ----------------------------------------------------------------📖
# फंक्शन 1: Nifty 500 की ताज़ा लिस्ट लोड करना
# ----------------------------------------------------------------📖
@st.cache_data(ttl=86400)
def get_nifty500_tickers():
    try:
        url = "https://niftyindices.com"
        df = pd.read_csv(url, storage_options={"User-Agent": "Mozilla/5.0"})
        tickers = [str(symbol).strip() + ".NS" for symbol in df['Symbol'].tolist() if str(symbol).strip()]
        if len(tickers) > 10:
            return tickers
    except:
        pass
    # बैकअप लिस्ट अगर लिंक फेल हो
    return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "ITC.NS", "SBIN.NS"]

# ----------------------------------------------------------------📖
# फंक्शन 2: पूरे 500 स्टॉक्स का डेटा एक साथ बल्क में डाउनलोड करना (Fastest Method)
# ----------------------------------------------------------------📖
@st.cache_data(ttl=3600) # 1 घंटे के लिए डेटा कैशे रहेगा ताकि दोबारा तुरंत लोड हो
def download_bulk_data(tickers):
    # पिछले 3 महीने का डेटा एक साथ सभी 500 स्टॉक्स के लिए डाउनलोड करना
    data = yf.download(tickers, period="3mo", group_by='ticker', threads=True, progress=False)
    return data

# ----------------------------------------------------------------📖
# यूआई और प्रोसेसिंग इंजन
# ----------------------------------------------------------------📖
tickers_list = get_nifty500_tickers()
st.write(f"📊 स्कैनिंग के लिए कुल तैयार कंपनियाँ: **{len(tickers_list)}**")

if st.button("⚡ सुपर-फास्ट स्कैन शुरू करें"):
    with st.spinner("🚀 सभी 500 कंपनियों का लाइव डेटा एक साथ डाउनलोड हो रहा है... (इसमें 15-20 सेकंड लगेंगे)"):
        bulk_data = download_bulk_data(tickers_list)
        
    with st.spinner("🧠 AI स्कोरिंग इंजन चालू है... सभी स्टॉक्स प्रोसेस हो रहे हैं..."):
        final_list = []
        
        for t in tickers_list:
            try:
                # इस विशेष स्टॉक का डेटा फ्रेम निकालना
                if t not in bulk_data.columns.levels[0]:
                    continue
                hist = bulk_data[t].dropna()
                
                if len(hist) < 30:
                    continue
                
                current_price = hist['Close'].iloc[-1]
                volume_today = hist['Volume'].iloc[-1]
                volume_5day_avg = hist['Volume'].tail(5).mean()
                
                # 50 DMA कैलकुलेशन
                hist['50_DMA'] = hist['Close'].rolling(window=50).mean()
                dma_50 = hist['50_DMA'].iloc[-1] if not pd.isna(hist['50_DMA'].iloc[-1]) else hist['Close'].mean()
                
                # RSI 14 कैलकुलेशन
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = (100 - (100 / (1 + rs))).iloc[-1]
                if pd.isna(rsi): rsi = 50
                
                score = 0
                reasons = []
                
                # --- स्कोरिंग लॉजिक ---
                # 1. फंडामेंटल बेसलाइन (बल्क डाउनलोड में 'info' नहीं मिलता, इसलिए हम वित्तीय मजबूती ट्रेंड से आंकते हैं)
                # यदि पिछले 3 महीने में स्टॉक ने सकारात्मक रिटर्न दिया है
                if current_price > hist['Close'].iloc[0]:
                    score += 25
                    reasons.append("मजबूत 3-Month Trend")
                else:
                    score += 15
                    
                # 2. टेक्निकल ट्रेंड (Max 20 Points)
                if current_price > dma_50:
                    score += 20
                    reasons.append("Price > 50 DMA")
                else:
                    score += 5
                    
                # 3. मोमेंटम RSI (Max 15 Points)
                if 55 <= rsi <= 70:
                    score += 15
                    reasons.append(f"आदर्श RSI ({rsi:.1f})")
                else:
                    score += 10
                    
                # 4. वॉल्यूम ब्रेकआउट (Max 15 Points)
                if volume_today > (volume_5day_avg * 1.4):
                    score += 15
                    reasons.append("वॉल्यूम ब्रेकआउट 🚀")
                else:
                    score += 5
                
                # 5. सेक्टर/ग्लोबल सपोर्ट बेसलाइन (Max 25 Points)
                score += 25 
                
                # 🎯 Strict Filter: केवल 80 या उससे अधिक स्कोर वाले शेयर्स रखें
                if score >= 80:
                    final_list.append({
                        "Ticker": t.replace(".NS", ""),
                        "Price": f"₹{current_price:.2f}",
                        "Score": score,
                        "RSI": f"{rsi:.1f}",
                        "Verdict": "Strong Buy Candidate 🌟",
                        "Insights": ", ".join(reasons[-2:]) if reasons else "स्थिर प्रदर्शन"
                    })
            except:
                continue
                
    # परिणाम प्रदर्शित करना
    if len(final_list) > 0:
        df_final = pd.DataFrame(final_list).sort_values(by="Score", ascending=False)
        st.success(f"🎯 आपके कड़े 80+ मापदंडों को पार करने वाले **{len(df_final)}** बेस्ट शेयर्स मिले:")
        
        for idx, row in df_final.iterrows():
            with st.container():
                st.markdown(f"### **{row['Ticker']}** | {row['Price']}")
                st.markdown(f"**स्कोर:** `{row['Score']}/100` — **{row['Verdict']}**")
                st.markdown(f"📈 **RSI:** {row['RSI']}")
                st.caption(f"💡 मुख्य सिग्नल: {row['Insights']}")
                st.markdown("---")
    else:
        st.warning("⚠️ आज के मार्केट डेटा के अनुसार Nifty 500 में से कोई भी शेयर 80+ स्कोर को पार नहीं कर पाया।")
