import streamlit as st
import requests
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. DATABASE SETUP (Memory Feature) ---
# This creates a local file 'user_memory.db' to store how you talk
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
st.set_page_config(page_title="NEXUS AI", layout="wide")
NEWS_API_KEY ="434fc8e864e04c43a7e07cdbce6d8fdb" if "NEWS_API_KEY" in st.secrets else "YOUR_NEWS_API_KEY"
HF_TOKEN ="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" if "HF_TOKEN" in st.secrets else "YOUR_HF_TOKEN"

# --- 3. COOL GRAPHIC STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .nav-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #334155;
        margin-bottom: 20px;
    }
    .stButton>button {
        border-radius: 8px;
        background: #3b82f6;
        color: white;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover { background: #60a5fa; transform: scale(1.02); }
    .arg-box {
        background: #1e1b4b;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #818cf8;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. CORE ENGINES ---
def fetch_news(query=None, source=None, mode="everything"):
    base_url = "https://newsapi.org/v2/"
    params = {"apiKey": NEWS_API_KEY, "language": "en"}
    
    if source: # Feature: Manual Company Selection
        endpoint = "top-headlines"
        params["sources"] = source
    elif query: # Feature: Search Subject
        endpoint = "everything"
        params["qInTitle"] = query
        params["sortBy"] = "relevancy"
    else: # Feature: Analysis of all
        endpoint = "top-headlines"
        params["category"] = "general"
        
    try:
        r = requests.get(base_url + endpoint, params=params)
        return r.json().get('articles', [])
    except:
        return []

def ai_engine(prompt, task="summarize"):
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    # Adding Memory Context to make arguments "Efficient"
    personality = get_personality_context()
    contextual_prompt = f"User style history: {personality}. Task: {task}. Content: {prompt}"
    
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": contextual_prompt, "options": {"wait_for_model": True}})
        res = response.json()
        return res[0]['summary_text'] if isinstance(res, list) else "Intelligence unit processing..."
    except:
        return "Connection to AI Nexus failed."

# --- 5. UI INTERFACE ---
st.title("🌐 NEXUS INTELLIGENCE")
tabs = st.tabs(["📡 Live Feed", "🔍 Deep Search", "🛡️ Debate Unit", "🧠 Memory"])

# --- TAB 1: LIVE FEED & COMPANY PICKER ---
with tabs[0]:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader("Source Selection")
        company = st.selectbox("Pick a Desk", ["All Sources", "bbc-news", "reuters", "the-verge", "bloomberg", "google-news"])
        source_id = None if company == "All Sources" else company
        
    with col2:
        articles = fetch_news(source=source_id)
        if articles:
            summary = ai_engine(" ".join([a['title'] for a in articles[:5]]), "Analysis of global streams")
            st.markdown(f"<div class='nav-card'><b>AI TREND ANALYSIS:</b><br>{summary}</div>", unsafe_allow_html=True)
            
            for a in articles[:5]:
                st.write(f"### {a['title']}")
                st.caption(f"{a['source']['name']} | {a['publishedAt']}")
                st.write(a['description'])
                st.markdown(f"[Read Full Intelligence]({a['url']})")
                st.divider()

# --- TAB 2: SUBJECT SEARCH ---
with tabs[1]:
    query = st.text_input("Enter Subject (e.g., 'Artificial Intelligence', 'Tesla', 'SpaceX')")
    search_mode = st.radio("Analysis Depth", ["Summary Only", "Full Report List"])
    
    if query:
        results = fetch_news(query=query)
        if search_mode == "Summary Only":
            text = " ".join([r['title'] for r in results[:10]])
            st.info(ai_engine(text, "Summarizing deep search results"))
        else:
            for r in results[:5]:
                st.write(f"**{r['title']}**")
                st.write(r['description'])

# --- TAB 3: DEBATE UNIT (The "Disagree" Feature) ---
with tabs[2]:
    st.subheader("Challenge the AI")
    topic = st.text_input("What topic shall we debate?")
    user_argument = st.text_area("State your position:")
    
    if st.button("INITIATE ARGUMENT"):
        # AI creates a counter-argument based on news data
        news_context = fetch_news(query=topic)
        context_str = " ".join([n['title'] for n in news_context[:3]])
        
        prompt = f"The user says: {user_argument}. Use this news context: {context_str}. Argue against the user effectively."
        ai_rebuttal = ai_engine(prompt, task="Refute and debate")
        
        st.markdown(f"<div class='arg-box'><b>AI REBUTTAL:</b><br>{ai_rebuttal}</div>", unsafe_allow_html=True)
        
        # SAVE TO MEMORY
        save_interaction(user_argument, ai_rebuttal, topic)
        st.success("Interaction saved to local memory. Future arguments will adapt to your style.")

# --- TAB 4: MEMORY ---
with tabs[3]:
    st.subheader("Your Intelligence Profile")
    st.write("The AI analyzes your past arguments to understand your logic patterns.")
    conn = sqlite3.connect('user_memory.db')
    history = pd.read_sql_query("SELECT * FROM memory", conn)
    st.dataframe(history)