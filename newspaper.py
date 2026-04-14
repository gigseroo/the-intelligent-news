import streamlit as st
import requests
import sqlite3
from datetime import datetime

# --- 1. CORE CONFIG ---
st.set_page_config(page_title="Neural Intel", layout="wide")

# Retrieve keys from Streamlit Secrets
NEWS_KEY = st.secrets.get("NEWS_API_KEY", "")
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

# --- 2. DEVICE-LOCAL MEMORY (Simplified for Mobile) ---
def save_to_brain(user_val, ai_val):
    try:
        conn = sqlite3.connect('local_memory.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS brain (ts TEXT, u TEXT, a TEXT)')
        c.execute("INSERT INTO brain VALUES (?,?,?)", (datetime.now().isoformat(), user_val, ai_val))
        conn.commit()
        conn.close()
    except:
        pass # Fails silently if device storage is restricted

# --- 3. UI ENGINE ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #e0e0e0; }
    header, footer, [data-testid="stHeader"] { visibility: hidden !important; }
    
    /* News Cards */
    .news-card {
        background: #111;
        border: 1px solid #222;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 12px;
        border-left: 4px solid #05ffa1;
    }
    
    /* Bubbles */
    .user-box {
        background: #222;
        padding: 12px;
        border-radius: 15px 15px 0 15px;
        margin: 5px 0 5px auto;
        width: fit-content;
        max-width: 85%;
    }
    .ai-box {
        background: linear-gradient(135deg, #05ffa1, #007aff);
        color: #000;
        padding: 12px;
        border-radius: 15px 15px 15px 0;
        margin: 5px auto 5px 0;
        width: fit-content;
        max-width: 85%;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. API LOGIC ---
def get_news(query=None, source=None):
    headers = {"User-Agent": "Mozilla/5.0"}
    base = "https://newsapi.org/v2/top-headlines?language=en&apiKey=" + NEWS_KEY
    if source and source != "All":
        url = f"https://newsapi.org/v2/top-headlines?sources={source}&apiKey={NEWS_KEY}"
    elif query:
        url = f"https://newsapi.org/v2/everything?q={query}&apiKey={NEWS_KEY}"
    else:
        url = base
    
    try:
        r = requests.get(url, headers=headers).json()
        return r.get('articles', [])
    except:
        return []

def call_ai(prompt, system_role="You are a helpful analyst."):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_role},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        res = requests.post(url, headers=headers, json=payload).json()
        return res['choices'][0]['message']['content']
    except:
        return "Neural connection failed."

# --- 5. THE APP INTERFACE ---
st.title("NEURAL INTEL")

tab1, tab2 = st.tabs(["SIGNAL FEED", "DEBATE UNIT"])

with tab1:
    # Manual Source & Search Selection
    c1, c2 = st.columns([1, 1])
    with c1:
        src = st.selectbox("Company", ["All", "bbc-news", "reuters", "bloomberg", "techcrunch", "the-verge"])
    with c2:
        find = st.text_input("Search Subject")
    
    # Summary Action
    if st.button("Generate Summary Analysis"):
        raw = get_news(find, src)
        titles = " ".join([t['title'] for t in raw[:10]])
        summary = call_ai("Summarize this news in 3 bullet points: " + titles)
        st.info(summary)

    # Feed Display
    arts = get_news(find, src)
    if arts:
        for a in arts:
            st.markdown(f"""<div class="news-card">
                <small style="color:#05ffa1">{a['source']['name']}</small><br>
                <b>{a['title']}</b><br>
                <span style="font-size:12px; color:#888;">{a.get('description') or ''}</span>
            </div>""", unsafe_allow_html=True)

with tab2:
    if "chat" not in st.session_state:
        st.session_state.chat = []

    # Display Chat
    for m in st.session_state.chat:
        style = "user-box" if m["role"] == "user" else "ai-box"
        st.markdown(f'<div class="{style}">{m["content"]}</div>', unsafe_allow_html=True)

    # Input area
    user_in = st.chat_input("State your argument...")
    if user_in:
        st.session_state.chat.append({"role": "user", "content": user_in})
        
        # Debate AI Logic
        with st.spinner("Counter-arguing..."):
            ai_out = call_ai(user_in, "Argue aggressively against the user's point. Be logical but firm.")
            st.session_state.chat.append({"role": "assistant", "content": ai_out})
            save_to_brain(user_in, ai_out)
        st.rerun()

    if st.button("Clear Device Memory"):
        st.session_state.chat = []
        st.rerun()