import streamlit as st
import requests
import sqlite3
from datetime import datetime

# --- 1. CORE CONFIG ---
st.set_page_config(page_title="Neural Intel", layout="wide")

NEWS_KEY = st.secrets.get("NEWS_API_KEY", "")
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

# --- 2. DEVICE-LOCAL MEMORY ---
def save_to_brain(u, a):
    try:
        conn = sqlite3.connect('local_memory.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS brain (ts TEXT, u TEXT, a TEXT)')
        c.execute("INSERT INTO brain VALUES (?,?,?)", (datetime.now().isoformat(), u, a))
        conn.commit()
        conn.close()
    except: pass

# --- 3. UI STYLE ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #e0e0e0; }
    header, footer, [data-testid="stHeader"] { visibility: hidden !important; }
    
    /* General News Cards with Images */
    .gen-card {
        background: #111;
        border-radius: 15px;
        overflow: hidden;
        margin-bottom: 20px;
        border: 1px solid #222;
    }
    .gen-img { width: 100%; height: 200px; object-fit: cover; }
    .gen-content { padding: 15px; }

    /* Debate Bubbles */
    .user-box {
        background: #222;
        padding: 12px;
        border-radius: 15px 15px 0 15px;
        margin: 5px 0 5px auto;
        width: fit-content;
        max-width: 85%;
        border: 1px solid #333;
    }
    .ai-box {
        background: linear-gradient(135deg, #05ffa1, #007aff);
        color: #000;
        padding: 12px;
        border-radius: 15px 15px 15px 0;
        margin: 5px auto 5px 0;
        width: fit-content;
        max-width: 85%;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. API LOGIC ---
def get_news(query=None, category="general"):
    headers = {"User-Agent": "Mozilla/5.0"}
    if query:
        url = f"https://newsapi.org/v2/everything?q={query}&apiKey={NEWS_KEY}&pageSize=10"
    else:
        url = f"https://newsapi.org/v2/top-headlines?country=us&category={category}&apiKey={NEWS_KEY}&pageSize=10"
    
    try:
        r = requests.get(url, headers=headers).json()
        return r.get('articles', [])
    except: return []

def call_ai(prompt, system_role):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_role},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6
    }
    try:
        res = requests.post(url, headers=headers, json=payload).json()
        return res['choices'][0]['message']['content']
    except: return "Link Error."

# --- 5. APP INTERFACE ---
st.title("NEURAL INTEL")

# General News is now the first tab (Start page)
tab1, tab2, tab3 = st.tabs(["GENERAL", "SEARCH", "DEBATE TIME"])

with tab1:
    st.markdown("### 🌎 Global Signal")
    arts = get_news() # Random top headlines
    if arts:
        for a in arts:
            if a.get('urlToImage'):
                st.markdown(f"""
                <div class="gen-card">
                    <img src="{a['urlToImage']}" class="gen-img">
                    <div class="gen-content">
                        <small style="color:#05ffa1">{a['source']['name']}</small><br>
                        <b>{a['title']}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

with tab2:
    search_query = st.text_input("Investigate Subject (e.g. NATO)")
    if search_query:
        with st.spinner("Analyzing signals..."):
            results = get_news(query=search_query)
            titles = " ".join([t['title'] for t in results[:5]])
            # Summarize the specific search
            summary = call_ai(f"Summarize recent news about {search_query} based on these titles: {titles}", 
                              "You are a concise intel analyst. Provide a 3-sentence summary.")
            st.info(summary)
            
            for r in results:
                st.write(f"**{r['title']}** — {r['source']['name']}")
                st.divider()

with tab3:
    if "chat" not in st.session_state: st.session_state.chat = []

    for m in st.session_state.chat:
        style = "user-box" if m["role"] == "user" else "ai-box"
        st.markdown(f'<div class="{style}">{m["content"]}</div>', unsafe_allow_html=True)

    user_in = st.chat_input("State your argument...")
    if user_in:
        st.session_state.chat.append({"role": "user", "content": user_in})
        with st.spinner("Processing..."):
            # System role enforces short, concise, 1-paragraph limit
            sys_role = "You are a sharp debater. Respond with a maximum of one short, concise, and informational paragraph. No filler."
            ai_out = call_ai(user_in, sys_role)
            st.session_state.chat.append({"role": "assistant", "content": ai_out})
            save_to_brain(user_in, ai_out)
        st.rerun()