import streamlit as st
import requests
import sqlite3
from datetime import datetime

# --- 1. CORE CONFIG ---
st.set_page_config(page_title="Intel Neural", layout="wide")

NEWS_KEY = st.secrets.get("NEWS_API_KEY", "")
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

# --- 2. THE STEALTH UI (NO HEADERS / NO FOOTERS) ---
st.markdown("""
    <style>
    /* 1. Kill the Top Gray Header and the 'Made with Streamlit' footer */
    header, footer, .stHeader, [data-testid="stHeader"], [data-testid="stFooter"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }
    
    /* 2. Remove padding from the top so it starts at the very edge */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }

    /* 3. Dark Theme & Background */
    .stApp { background-color: #050505; color: #e0e0e0; }

    /* 4. Visual News Cards */
    .gen-card {
        background: #111;
        border-radius: 15px;
        overflow: hidden;
        margin-bottom: 25px;
        border: 1px solid #222;
    }
    .gen-img { width: 100%; height: 220px; object-fit: cover; border-bottom: 2px solid #05ffa1; }
    .gen-content { padding: 18px; }

    /* 5. Debate UI */
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
    .topic-lock {
        background: rgba(5, 255, 161, 0.1);
        padding: 12px; border-radius: 8px; border: 1px dashed #05ffa1;
        margin-bottom: 20px; text-align: center; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. API ENGINES ---
def get_intel(query=None):
    headers = {"User-Agent": "Mozilla/5.0"}
    # Using 'top-headlines' with 'language=en' is the most reliable for General News
    if query:
        url = f"https://newsapi.org/v2/everything?q={query}&sortBy=relevance&apiKey={NEWS_KEY}&pageSize=15"
    else:
        url = f"https://newsapi.org/v2/top-headlines?language=en&apiKey={NEWS_KEY}&pageSize=15"
    
    try:
        r = requests.get(url, headers=headers).json()
        return r.get('articles', [])
    except: return []

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
    except: return "Neural Link Timeout."

# --- 4. APP INTERFACE ---
# We keep the Tabs, but the styling above hides the gray area they usually sit in
tab1, tab2, tab3 = st.tabs(["GENERAL", "SEARCH", "DEBATE TIME"])

with tab1:
    st.markdown("<br>", unsafe_allow_html=True) # Small gap since header is gone
    general_news = get_intel() 
    if general_news:
        for a in general_news:
            if a.get('urlToImage'): # Only show news with pictures for the "Main" vibe
                st.markdown(f"""
                <div class="gen-card">
                    <img src="{a['urlToImage']}" class="gen-img">
                    <div class="gen-content">
                        <small style="color:#05ffa1">{a['source']['name'].upper()}</small><br>
                        <b style="font-size:18px">{a['title']}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

with tab2:
    s_input = st.text_input("Investigate Anything")
    if s_input:
        with st.spinner("Processing Report..."):
            data = get_intel(s_input)
            context = " ".join([t['title'] for t in data[:15]])
            report = call_ai(
                f"Provide a deep-dive comprehensive report on {s_input} using these headlines: {context}",
                "You are an elite analyst. Provide a massive, detailed intelligence report. No length limits."
            )
            st.markdown(f"### 📊 Report: {s_input}")
            st.write(report)

with tab3:
    # Separate Subject and Argument inputs
    fixed_subject = st.text_input("SET SUBJECT")
    
    if fixed_subject:
        st.markdown(f"<div class='topic-lock'>TOPIC: {fixed_subject.upper()}</div>", unsafe_allow_html=True)
        
        if "debate_chat" not in st.session_state: st.session_state.debate_chat = []

        for m in st.session_state.debate_chat:
            style = "user-box" if m["role"] == "user" else "ai-box"
            st.markdown(f'<div class="{style}">{m["content"]}</div>', unsafe_allow_html=True)

        user_arg = st.chat_input("Enter Argument")
        if user_arg:
            st.session_state.debate_chat.append({"role": "user", "content": user_arg})
            with st.spinner(""):
                sys = f"You are a sharp debater. Subject: {fixed_subject}. Stick to it. 1 concise paragraph max."
                ans = call_ai(user_arg, sys)
                st.session_state.debate_chat.append({"role": "assistant", "content": ans})
            st.rerun()