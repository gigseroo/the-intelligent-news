import streamlit as st
import requests
import sqlite3
import pandas as pd
from datetime import datetime
import time

# --- 1. DATABASE ---
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

# --- 2. CONFIG ---
st.set_page_config(page_title="Intelligence News", layout="wide")
NEWS_KEY = "434fc8e864e04c43a7e07cdbce6d8fdb"
HF_KEY = "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"

# --- 3. UI STYLE ---
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        overscroll-behavior-y: none !important;
    }
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .news-card { 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #30363d; 
        margin-bottom: 20px; 
        background: #161b22;
    }
    .source-tag {
        background: #238636;
        color: white;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
        margin-bottom: 10px;
        width: fit-content;
    }
    img { border-radius: 10px; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ENGINE ---
def get_news(q=None, s=None):
    url = "https://newsapi.org/v2/top-headlines" if not q else "https://newsapi.org/v2/everything"
    p = {"apiKey": NEWS_KEY, "language": "en", "pageSize": 10}
    if s: p["sources"] = s
    if q: p["q"] = q
    try:
        r = requests.get(url, params=p).json()
        return r.get('articles', [])
    except: return []

def ask_ai(txt, task):
    # SWITCHED TO FLAN-T5: It's faster for debating/logic
    API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
    headers = {"Authorization": f"Bearer {HF_KEY}"}
    
    # We define a clearer prompt for the AI
    payload = {
        "inputs": f"Task: {task}. Based on this context: {txt[:800]}, provide a detailed response.",
        "options": {"wait_for_model": True}
    }
    
    # INTERNAL RETRY LOOP (Stops the "Try again in 10s" manual clicking)
    for attempt in range(6):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=40)
            res = response.json()
            
            if isinstance(res, list) and 'generated_text' in res[0]:
                return res[0]['generated_text']
            elif isinstance(res, dict) and 'generated_text' in res:
                return res['generated_text']
            elif "estimated_time" in str(res):
                time.sleep(8)
                continue
        except:
            time.sleep(3)
            continue
            
    return "The Intelligence Unit is overloaded. Please try once more in 30 seconds."

# --- 5. APP ---
st.title("Intelligence News")
t1, t2, t3, t4 = st.tabs(["Feed", "Search", "Debate", "History"])

# --- TAB 1: FEED ---
with t1:
    src = st.selectbox("Agency", ["All", "bbc-news", "reuters", "the-verge", "bloomberg"])
    news = get_news(s=None if src == "All" else src)
    
    if news:
        for n in news[:8]:
            st.markdown(f"<div class='news-card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='source-tag'>{n['source']['name']}</div>", unsafe_allow_html=True)
            if n.get('urlToImage'):
                st.image(n['urlToImage'])
            st.subheader(n['title'])
            st.write(n['description'])
            st.markdown(f"[Read Full Intel]({n['url']})")
            st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2: SEARCH ---
with t2:
    query = st.text_input("Enter Subject to Search")
    if query:
        res = get_news(q=query)
        if res:
            for r in res[:6]:
                st.markdown(f"<div class='news-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='source-tag'>Source: {r['source']['name']}</div>", unsafe_allow_html=True)
                st.write(f"### {r['title']}")
                # Bigger summaries by showing more content if available
                body = r.get('content') or r.get('description') or "No summary available."
                st.write(body[:400] + "...") 
                st.markdown(f"[Click here for Full Article]({r['url']})")
                st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 3: DEBATE ---
with t3:
    st.subheader("Debate Mode")
    topic = st.text_input("Debate Topic")
    arg = st.text_area("Your Argument")
    
    if st.button("Fight"):
        if not topic or not arg:
            st.warning("Please provide a topic and an argument.")
        else:
            with st.status("Engaging AI... This may take 20 seconds", expanded=True) as status:
                # Fetching real news context for the debate
                context_news = get_news(q=topic)
                ctx_str = " ".join([n['title'] for n in context_news[:3]])
                
                # Logic for the AI
                debate_prompt = f"The user thinks: {arg}. Use this news info: {ctx_str}. Formulate a strong, logical counter-argument."
                reply = ask_ai(debate_prompt, "Argue against the user")
                
                st.session_state['rebuttal'] = reply
                save_mem(arg, reply, topic)
                status.update(label="Debate ready!", state="complete")
            
    if 'rebuttal' in st.session_state:
        st.error(f"AI Counter-Argument: {st.session_state['rebuttal']}")

# --- TAB 4: HISTORY ---
with t4:
    try:
        conn = sqlite3.connect('intel.db')
        st.dataframe(pd.read_sql_query("SELECT * FROM logs ORDER BY time DESC", conn), use_container_width=True)
        conn.close()
    except: st.write("History log is currently empty.")