import streamlit as st
import requests
import sqlite3
import pandas as pd
from datetime import datetime
import time

# --- 1. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('user_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS memory 
                 (timestamp TEXT, user_input TEXT, ai_response TEXT, topic TEXT)''')
    conn.commit()
    conn.close()

def save_interaction(user_text, ai_text, topic):
    conn = sqlite3.connect('user_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO memory VALUES (?,?,?,?)", 
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_text, ai_text, topic))
    conn.commit()
    conn.close()

def get_personality_context():
    try:
        conn = sqlite3.connect('user_memory.db')
        df = pd.read_sql_query("SELECT user_input FROM memory ORDER BY timestamp DESC LIMIT 5", conn)
        conn.close()
        return " ".join(df['user_input'].tolist())
    except:
        return ""

init_db()

# --- 2. CONFIG & KEYS ---
st.set_page_config(page_title="News", layout="wide")

# It is recommended to set these in the Streamlit Cloud Secrets dashboard
NEWS_API_KEY ="434fc8e864e04c43a7e07cdbce6d8fdb" if "NEWS_API_KEY" in st.secrets else "YOUR_NEWS_API_KEY"
HF_TOKEN ="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" if "HF_TOKEN" in st.secrets else "YOUR_HF_TOKEN"

# --- 3. CLEAN STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .nav-card {
        background: #1e293b;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #334155;
        margin-bottom: 20px;
    }
    .stButton>button {
        border-radius: 4px;
        background: #3b82f6;
        color: white;
        border: none;
    }
    .arg-box {
        background: #1e1b4b;
        padding: 20px;
        border-radius: 8px;
        border-left: 5px solid #818cf8;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. CORE ENGINES ---
def fetch_news(query=None, source=None):
    base_url = "https://newsapi.org/v2/"
    params = {"apiKey": NEWS_API_KEY, "language": "en"}
    
    if source:
        endpoint = "top-headlines"
        params["sources"] = source
    elif query:
        endpoint = "everything"
        params["qInTitle"] = query
        params["sortBy"] = "relevancy"
    else:
        endpoint = "top-headlines"
        params["category"] = "general"
        
    try:
        r = requests.get(base_url + endpoint, params=params)
        return r.json().get('articles', [])
    except:
        return []

def ai_engine(prompt, task="summarize"):
    # Using a lighter model for faster response times
    API_URL = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    personality = get_personality_context()
    contextual_prompt = f"Style history: {personality}. Task: {task}. Content: {prompt[:600]}"
    
    for attempt in range(3):
        try:
            response = requests.post(
                API_URL, 
                headers=headers, 
                json={"inputs": contextual_prompt, "options": {"wait_for_model": True}},
                timeout=25
            )
            res = response.json()
            
            if isinstance(res, dict) and "estimated_time" in res:
                st.info(f"System warming up... remaining: {round(res['estimated_time'], 1)}s")
                time.sleep(5)
                continue
                
            if isinstance(res, list) and len(res) > 0:
                return res[0]['summary_text']
            
            return "Intelligence processed. Please refresh to view."
            
        except:
            if attempt < 2:
                time.sleep(2)
                continue
            return "Connection timeout. The server is busy. Please try again."
            
    return "Intelligence unit unresponsive."

# --- 5. UI INTERFACE ---
st.title("Nexus Intelligence News")
tabs = st.tabs(["Live Feed", "Deep Search", "Debate Unit", "Memory"])

# --- TAB 1: LIVE FEED ---
with tabs[0]:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader("Source Selection")
        company = st.selectbox("Select Agency", ["All Sources", "bbc-news", "reuters", "the-verge", "bloomberg", "google-news"])
        source_id = None if company == "All Sources" else company
        
    with col2:
        articles = fetch_news(source=source_id)
        if articles:
            # Create a combined summary of the top headlines
            headline_blob = " ".join([a['title'] for a in articles[:5]])
            summary = ai_engine(headline_blob, "General Analysis")
            st.markdown(f"<div class='nav-card'><b>Executive Summary:</b><br>{summary}</div>", unsafe_allow_html=True)
            
            for a in articles[:5]:
                st.write(f"### {a['title']}")
                st.caption(f"{a['source']['name']} | {a['publishedAt']}")
                st.write(a['description'])
                st.markdown(f"[View Document]({a['url']})")
                st.divider()

# --- TAB 2: DEEP SEARCH ---
with tabs[1]:
    query = st.text_input("Search Subject")
    search_mode = st.radio("Intelligence Depth", ["Summary Only", "Full Report List"])
    
    if query:
        results = fetch_news(query=query)
        if search_mode == "Summary Only":
            text = " ".join([r['title'] for r in results[:10]])
            st.info(ai_engine(text, "Search Result Summary"))
        else:
            for r in results[:5]:
                st.write(f"**{r['title']}**")
                st.write(r['description'])

# --- TAB 3: DEBATE UNIT ---
with tabs[2]:
    st.subheader("Counter-Intelligence Debate")
    topic = st.text_input("Debate Topic")
    user_argument = st.text_area("Your Position")
    
    if st.button("Initiate Debate"):
        news_context = fetch_news(query=topic)
        context_str = " ".join([n['title'] for n in news_context[:3]])
        
        prompt = f"User argues: {user_argument}. Context: {context_str}. Provide a logical counter-argument."
        ai_rebuttal = ai_engine(prompt, task="Debate")
        
        st.markdown(f"<div class='arg-box'><b>AI Rebuttal:</b><br>{ai_rebuttal}</div>", unsafe_allow_html=True)
        save_interaction(user_argument, ai_rebuttal, topic)

# --- TAB 4: MEMORY ---
with tabs[3]:
    st.subheader("Stored Intelligence Patterns")
    st.write("Reviewing saved logic and speech patterns.")
    try:
        conn = sqlite3.connect('user_memory.db')
        history = pd.read_sql_query("SELECT * FROM memory", conn)
        st.dataframe(history)
        conn.close()
    except:
        st.write("Memory logs currently empty.")