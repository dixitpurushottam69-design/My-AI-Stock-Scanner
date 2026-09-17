import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

# मोबाइल व्यू सेटिंग्स
st.set_page_config(page_title="Nifty 500 70+ Scanner", page_icon="⚡", layout="centered")

st.title("⚡ AI Stock Scanner (70+ Watchlist Filter)")
st.write("Nifty 500 में से **Watchlist & Strong Buy (Score 70-100)** वाले शेयर्स की लिस्ट")

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
    # बैकअप लिस्ट
    return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "ITC.NS", "SBIN.NS"]

# ----------------------------------------------------------------📖
# फंक्शन 2: डेटा एक साथ बल्क में डाउनलोड करना
# ----------------------------------------------------------------📖
@st.cache_data(ttl=3600)
def download_bulk_data(tickers):
    data = yf.download(tickers, period="3mo", group_by='ticker', threads=True, progress=False)
    return data

# ----------------------------------------------------------------📖
# यूआई और प्रोसेसिंग इंजन
# ----------------------------------------------------------------📖
tickers_list = get_nifty500_tickers()
st.write(f"📊 स्कैनिंग के लिए कुल तैयार कंपनियाँ: **{len(tickers_list)}**")

if st.button("⚡ 70+ स्कोर वाले शेयर्स स्कैन करें"):
    with st.spinner("🚀 Nifty 500 का लाइव डेटा डाउनलोड हो रहा है... (इसमें 15-20 सेकंड लगेंगे)"):
        bulk_data = download_bulk_data(tickers_list)
        
    with st.spinner("🧠 AI स्कोरिंग इंजन चालू है... 70+ वाले शेयर्स फ़िल्टर किए जा रहे हैं..."):
        final_list = []
        
        for t in tickers_list:
            try:
                if t not in bulk_data.columns.levels:
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
                
                # --- 100-Point स्कोरिंग लॉजिक ---
                # 1. ट्रेंड मजबूती (Max 25 Points)
                if current_price > hist['Close'].iloc[0]:
                    score += 25
                    reasons.append("मजबूत 3-Month Trend")
                else:
                    score += 15
                    
                # 2. टेक्निकल 50 DMA (Max 20 Points) - चरण 14
                if current_price > dma_50:
                    score += 20
                    reasons.append("Price > 50 DMA")
                else:
                    score += 5
                    
                # 3. मोमेंटम RSI (Max 15 Points) - चरण 15
                if 55 <= rsi <= 70:
                    score += 15
                    reasons.append(f"आदर्श RSI ({rsi:.1f})")
                else:
                    score += 10
                    
                # 4. वॉल्यूम ब्रेकआउट (Max 15 Points) - चरण 17
                if volume_today > (volume_5day_avg * 1.4):
                    score += 15
                    reasons.append("वॉल्यूम ब्रेकआउट 🚀")
                else:
                    score += 5
                
                # 5. सेक्टर/ग्लोबल सपोर्ट बेसलाइन (Max 25 Points)
                score += 25 
                
                # 🎯 NEW FILTER: केवल 70 या उससे अधिक स्कोर वाले शेयर्स रखें
                if score >= 70:
                    # स्कोर के हिसाब से वर्डिक्ट तय करना
                    if score >= 80:
                        verdict = "Strong Buy Candidate 🌟"
                    else:
                        verdict = "Watchlist / Confirm होने दें ⏳"
                        
                    final_list.append({
                        "Ticker": t.replace(".NS", ""),
                        "Price": f"₹{current_price:.2f}",
                        "Score": score,
                        "RSI": f"{rsi:.1f}",
                        "Verdict": verdict,
                        "Insights": ", ".join(reasons[-2:]) if reasons else "स्थिर प्रदर्शन"
                    })
            except:
                continue
                
    # परिणाम प्रदर्शित करना
    if len(final_list) > 0:
        # सबसे हाई स्कोर वाले स्टॉक्स सबसे ऊपर दिखेंगे
        df_final = pd.DataFrame(final_list).sort_values(by="Score", ascending=False)
        st.success(f"🎯 आपके 70+ मापदंडों को पार करने वाले **{len(df_final)}** शेयर्स मिले:")
        
        for idx, row in df_final.iterrows():
            with st.container():
                # स्कोर के आधार पर अलग रंग का टैग या स्टार दिखाना
                emoji = "🌟" if row['Score'] >= 80 else "⏳"
                st.markdown(f"### **{row['Ticker']}** | {row['Price']}")
                st.markdown(f"**स्कोर:** `{row['Score']}/100` — **{row['Verdict']}**")
                st.markdown(f"📈 **RSI:** {row['RSI']}")
                st.caption(f"💡 मुख्य सिग्नल: {row['Insights']}")
                st.markdown("---")
    else:
        st.warning("⚠️ आज के मार्केट में कोई भी शेयर 70 स्कोर को भी पार नहीं कर पाया।")
