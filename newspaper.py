import streamlit as st
import requests

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="THE INTELLIGENT | MIDNIGHT", layout="wide")

# HIGHLIGHT: Paste your keys here
NEWS_API_KEY = "434fc8e864e04c43a7e07cdbce6d8fdb"
HF_TOKEN = "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" 

# --- 2. DARK MODE PROFESSIONAL STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@300;400;600&display=swap');
    
    .stApp {
        background-color: #05070a;
        color: #ffffff;
    }
    
    .main-title {
        font-family: 'Playfair Display', serif;
        text-align: center;
        font-size: 72px;
        color: #ffffff;
        margin-bottom: 0px;
        letter-spacing: -2px;
    }
    
    .header-bar {
        text-align: center;
        font-family: 'Inter', sans-serif;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 3px;
        border-top: 1px solid #1f2937;
        border-bottom: 1px solid #1f2937;
        padding: 10px 0;
        margin-bottom: 40px;
        color: #9ca3af;
    }
    
    h2, h3 {
        font-family: 'Playfair Display', serif !important;
        color: #ffffff !important;
        letter-spacing: -0.5px;
    }
    
    .stMarkdown p {
        font-family: 'Inter', sans-serif;
        font-weight: 300;
        line-height: 1.8;
        color: #d1d5db;
    }

    .briefing-box {
        background-color: #0f172a;
        padding: 25px;
        border-left: 4px solid #3b82f6;
        margin-bottom: 35px;
        border-radius: 0 4px 4px 0;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 0px;
        border: 1px solid #3b82f6;
        background-color: transparent;
        color: #3b82f6;
        text-transform: uppercase;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 2px;
        padding: 12px;
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #3b82f6;
        color: #ffffff;
        border: 1px solid #3b82f6;
    }

    hr {
        border: 0;
        border-top: 1px solid #1f2937;
        margin: 30px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. REFINED LOGIC (Better Relevance) ---

def fetch_news(search_query):
    # Use qInTitle to ensure the topic is the MAIN focus
    # Use sortBy=relevancy to get the biggest stories
    
    if not search_query or search_query in ["Global Markets", "American Politics", "British Politics", "Greek Politics"]:
        # Presets use Top Headlines for maximum quality
        country_map = {"American Politics": "us", "British Politics": "gb", "Greek Politics": "gr"}
        country = country_map.get(search_query, "us")
        url = f"https://newsapi.org/v2/top-headlines?country={country}&pageSize=12&apiKey={NEWS_API_KEY}"
    else:
        # Custom searches use Everything but prioritize headlines
        url = f"https://newsapi.org/v2/everything?qInTitle={search_query}&language=en&sortBy=relevancy&pageSize=12&apiKey={NEWS_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
        articles = data.get('articles', [])
        # Filter out broken or removed results
        return [a for a in articles if a.get('description') and a['title'] != "[Removed]"]
    except:
        return []

def summarize_news(articles):
    # Free model: facebook/bart-large-cnn
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    # Focus only on the top 5 most relevant stories for the summary
    combined_text = " ".join([f"Topic: {a['title']}. Details: {a['description']}" for a in articles[:5]])
    
    if len(combined_text) < 100:
        return "Intelligence stream insufficient for high-level synthesis."

    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": combined_text})
        result = response.json()
        if isinstance(result, list):
            return result[0]['summary_text']
        return "Synthesizing data... please refresh in 5 seconds."
    except:
        return "Editorial synthesis offline. View raw data below."

# --- 4. THE INTERFACE ---

st.markdown("<h1 class='main-title'>THE INTELLIGENT</h1>", unsafe_allow_html=True)
st.markdown('<div class="header-bar">DATASTREAM: ENCRYPTED | STRATEGIC INSIGHT | NO EMOJIS</div>', unsafe_allow_html=True)

# Sidebar
st.sidebar.title("INTELLIGENCE UNIT")
user_search = st.sidebar.text_input("QUERY DATABASE", placeholder="Search: Trump, NATO, Athens...")

st.sidebar.markdown("---")
preset = st.sidebar.radio("REGIONAL DESKS", ["Global Markets", "American Politics", "British Politics", "Greek Politics"])

final_query = user_search if user_search else preset

if st.button("INITIATE BRIEFING"):
    with st.spinner("FILTERING NOISE..."):
        news_data = fetch_news(final_query)
        
        if news_data:
            st.markdown(f"### EXECUTIVE BRIEFING: {final_query.upper()}")
            with st.container():
                summary = summarize_news(news_data)
                st.markdown(f"<div class='briefing-box'>{summary}</div>", unsafe_allow_html=True)
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            cols = st.columns(2)
            for i, art in enumerate(news_data[:10]):
                with cols[i % 2]:
                    st.subheader(art['title'])
                    if art.get('urlToImage'):
                        st.image(art['urlToImage'], use_container_width=True)
                    st.caption(f"{art['source']['name'].upper()} • {art['publishedAt'][:10]}")
                    st.write(art['description'])
                    st.markdown(f"[VIEW FULL INTEL]({art['url']})")
                    st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.error("DATABASE EMPTY: No relevant articles found for this query.")