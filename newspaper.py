import streamlit as st
import requests
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('intel.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS logs (time TEXT, user TEXT, ai TEXT, topic TEXT)')
    conn.commit()
    conn.close()

def save_mem(u, a, t):
    conn = sqlite3.connect('intel.db')
    c = conn.cursor()
    c.execute("INSERT INTO logs VALUES (?,?,?,?)", (datetime.now().strftime("%H:%M"), u, a, t))
    conn.commit()
    conn.close()

init_db()

# --- 2. CONFIGURATION ---
st.set_page_config(page_title="Intelligence News", layout="wide")
NEWS_KEY = st.secrets.get("NEWS_API_KEY", "")
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

# --- 3. WHATSAPP / INSTAGRAM STYLE CSS ---
st.markdown("""
    <style>
    html, body { overscroll-behavior-y: contain !important; background-color: #0d1117; }
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    
    /* Chat Container */
    .chat-container { display: flex; flex-direction: column; gap: 10px; padding: 10px; }
    
    /* User Bubble (Right-ish / Grey) */
    .user-bubble {
        align-self: flex-end;
        background-color: #30363d;
        color: white;
        padding: 10px 15px;
        border-radius: 18px 18px 2px 18px;
        max-width: 80%;
        margin-left: auto;
    }
    
    /* AI Bubble (Left-ish / Insta-Blue) */
    .ai-bubble {
        align-self: flex-start;
        background: linear-gradient(45deg, #007aff, #00c6ff);
        color: white;
        padding: 10px 15px;
        border-radius: 18px 18px 18px 2px;
        max-width: 80%;
        margin-right: auto;
    }

    .news-card { 
        padding: 20px; border-radius: 12px; border: 1px solid #30363d; 
        margin-bottom: 25px; background: #161b22; 
    }
    .source-tag {
        background: #238636; color: white; padding: 4px 12px;
        border-radius: 4px; font-size: 11px; font-weight: bold; margin-bottom: 12px;
        width: fit-content;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ENGINE FUNCTIONS ---
def get_news(q=None, s=None):
    url = "https://newsapi.org/v2/top-headlines" if not q else "https://newsapi.org/v2/everything"
    p = {"apiKey": NEWS_KEY, "language": "en", "pageSize": 10}
    if s: p["sources"] = s
    if q: p["q"] = q
    try:
        r = requests.get(url, params=p).json()
        return r.get('articles', [])
    except: return []

def ask_ai_groq(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    api_token = str(GROQ_KEY).strip().replace('"', '').replace("'", "")
    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
    
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        return response.json()['choices'][0]['message']['content']
    except:
        return "Intelligence connection lost. Try again."

# --- 5. INTERFACE ---
st.title("Intelligence News")
t1, t2, t3, t4 = st.tabs(["Feed", "Search", "Fight", "History"])

with t1:
    src = st.selectbox("Agency", ["All", "bbc-news", "reuters", "the-verge", "bloomberg"])
    news = get_news(s=None if src == "All" else src)
    if news:
        for n in news[:8]:
            st.markdown(f"<div class='news-card'><div class='source-tag'>{n['source']['name']}</div>", unsafe_allow_html=True)
            if n.get('urlToImage'): st.image(n['urlToImage'])
            st.subheader(n['title'])
            st.write(n['description'])
            st.markdown(f"[View Document]({n['url']})")
            st.markdown("</div>", unsafe_allow_html=True)

with t2:
    query = st.text_input("Investigate Topic")
    if query:
        res = get_news(q=query)
        for r in res[:5]:
            st.markdown(f"<div class='news-card'><div class='source-tag'>{r['source']['name']}</div>", unsafe_allow_html=True)
            st.subheader(r['title'])
            st.write((r.get('description') or "")[:300])
            st.markdown(f"[Read Intel]({r['url']})")
            st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 3: CHAT DEBATE ---
with t3:
    st.subheader("Counter-Intel Debate")
    
    # Initialize chat history if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_topic" not in st.session_state:
        st.session_state.current_topic = ""

    topic = st.text_input("Set Debate Topic", placeholder="e.g. AI safety, Politics, Sports")
    
    # Display Chat History
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for msg in st.session_state.messages:
        div_class = "user-bubble" if msg["role"] == "user" else "ai-bubble"
        st.markdown(f"<div class='{div_class}'>{msg['content']}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Chat Input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Your Response:", placeholder="Type your argument...")
        submit = st.form_submit_button("Send")

        if submit and user_input:
            # 1. Add user message to history
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # 2. Get AI Response
            with st.spinner("AI is typing..."):
                # Use current topic for context if available
                ctx_news = get_news(q=topic) if topic else []
                ctx_str = ctx_news[0]['title'] if ctx_news else "current affairs"
                
                # Build the prompt with history
                system_prompt = {"role": "system", "content": f"You are a sharp debater. Context: {ctx_str}. Keep it under 3 sentences."}
                full_history = [system_prompt] + st.session_state.messages
                
                ai_reply = ask_ai_groq(full_history)
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                save_mem(user_input, ai_reply, topic)
                
            st.rerun()

    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

with t4:
    try:
        conn = sqlite3.connect('intel.db')
        df = pd.read_sql_query("SELECT * FROM logs ORDER BY time DESC", conn)
        st.dataframe(df, use_container_width=True)
        conn.close()
    except: st.write("Logs empty.")