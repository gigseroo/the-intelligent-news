import streamlit as st
import requests
import sqlite3
from datetime import datetime

# --- 1. CORE CONFIG ---
st.set_page_config(page_title="Intel Neural", layout="wide", initial_sidebar_state="collapsed")

NEWS_KEY = st.secrets.get("NEWS_API_KEY", "")
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

# --- 2. THE TOTAL STEALTH UI ---
st.markdown("""
    <style>
    /* Absolute Kill of Header and Footer */
    [data-testid="stHeader"], [data-testid="stFooter"], header, footer, .st-emotion-cache-18ni7ap {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Remove the 'top gap' so it looks like a native APK */
    .stAppViewBlockContainer {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }
    
    .stApp { background-color: #050505; color: #e0e0e0; }

    /* Visual News Cards */
    .gen-card {
        background: #111;
        border-radius: 15px;
        overflow: hidden;
        margin-bottom: 25px;
        border: 1px solid #222;
    }
    .gen-img { width: 100%; height: 240px; object-fit: cover; border-bottom: 2px solid #05ffa1; }
    .gen-content { padding: 18px; }

    /* Debate Boxes */
    .ai-box {
        background: linear-gradient(135deg, #05ffa1, #007aff);
        color: #000; padding: 15px; border-radius: 15px;
        margin: 10px 0; font-weight: 600;
    }
    .user-box {
        background: #222; color: #fff; padding: 15px; border-radius: 15px;
        margin: 10px 0 10px auto; width: fit-content; max-width: 85%;
        border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. API ENGINES ---
def get_intel(query=None):
    headers = {"User-Agent": "Mozilla/5.0"}
    # If no query, we search for 'breaking news' to ensure we get results with images
    search_term = query if query else "breaking news"
    url = f"https://newsapi.org/v2/everything?q={search_term}&language=en&sortBy=publishedAt&apiKey={NEWS_KEY}&pageSize=20"
    
    try:
        r = requests.get(url, headers=headers).json()
        articles = r.get('articles', [])
        # Filter: Only return articles that actually have images for the General feed
        return [a for a in articles if a.get('urlToImage')]
    except:
        return []

def call_ai(prompt, system_role):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": system_role}, {"role": "user", "content": prompt}],
        "temperature": 0.6
    }
    try:
        res = requests.post(url, headers=headers, json=payload).json()
        return res['choices'][0]['message']['content']
    except:
        return "Neural Link Timeout."

# --- 4. APP INTERFACE ---
tab1, tab2, tab3 = st.tabs(["GENERAL", "SEARCH", "DEBATE TIME"])

with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    general_news = get_intel() 
    if general_news:
        for a in general_news:
            st.markdown(f"""
            <div class="gen-card">
                <img src="{a['urlToImage']}" class="gen-img">
                <div class="gen-content">
                    <small style="color:#05ffa1">{a['source']['name'].upper()}</small><br>
                    <b style="font-size:18px">{a['title']}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("📡 Scanning for signals... Ensure NEWS_API_KEY is in Secrets.")

with tab2:
    s_input = st.text_input("Investigate Subject")
    if s_input:
        with st.spinner("Aggregating Intelligence..."):
            data = get_intel(s_input)
            context = " ".join([t['title'] for t in data[:15]])
            report = call_ai(
                f"Deep-dive report on {s_input}: {context}",
                "You are an elite analyst. Provide a massive, detailed, multi-paragraph report. No length limits."
            )
            st.markdown(f"### 📊 Report: {s_input}")
            st.write(report)

with tab3:
    fixed_subject = st.text_input("SET SUBJECT")
    if fixed_subject:
        if "debate_chat" not in st.session_state: st.session_state.debate_chat = []

        for m in st.session_state.debate_chat:
            style = "user-box" if m["role"] == "user" else "ai-box"
            st.markdown(f'<div class="{style}">{m["content"]}</div>', unsafe_allow_html=True)

        user_arg = st.chat_input("Enter Argument")
        if user_arg:
            st.session_state.debate_chat.append({"role": "user", "content": user_arg})
            with st.spinner(""):
                sys = f"Sharp debater. Subject: {fixed_subject}. Stick to it. 1 paragraph max."
                ans = call_ai(user_arg, sys)
                st.session_state.debate_chat.append({"role": "assistant", "content": ans})
            st.rerun()