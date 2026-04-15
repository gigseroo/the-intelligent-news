import streamlit as st
import requests
import urllib.parse

# --- 1. THE "BOUTIQUE HUD" UI ---
st.set_page_config(page_title="G.R.E.G. COMMAND", layout="wide")

st.markdown("""
    <style>
    [data-testid="stHeader"], [data-testid="stFooter"], header, footer { display: none !important; }
    .stApp { background-color: #020508; color: #00f2ff; font-family: 'Inter', sans-serif; }
    
    /* Product Card Styling */
    .product-card {
        background: rgba(0, 242, 255, 0.05);
        border: 1px solid rgba(0, 242, 255, 0.2);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 20px;
        transition: 0.3s;
    }
    .product-card:hover { border-color: #00f2ff; box-shadow: 0 0 15px rgba(0, 242, 255, 0.3); }
    .price-tag { color: #00ff88; font-weight: bold; font-size: 20px; }
    
    /* GREG Avatar */
    .greg-status {
        background: #00f2ff; color: #000;
        padding: 5px 15px; border-radius: 20px;
        font-size: 12px; font-weight: bold;
        display: inline-block; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE BRAIN ---
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

def greg_ai(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": "You are GREG. Efficient, helpful, and high-tech."}, 
                     {"role": "user", "content": prompt}]
    }
    try:
        res = requests.post(url, headers=headers, json=payload).json()
        return res['choices'][0]['message']['content']
    except: return "Connection unstable, Sir."

# --- 3. SESSION STATE ---
if "shopping_cart" not in st.session_state: st.session_state.shopping_cart = []
if "view" not in st.session_state: st.session_state.view = "main"

# --- 4. THE INTERFACE ---
st.markdown('<div class="greg-status">G.R.E.G. ONLINE // TACTICAL SHOPPER</div>', unsafe_allow_html=True)

# SIDEBAR: PERSISTENT SEARCH
with st.sidebar:
    st.title("G.R.E.G.")
    search_input = st.text_input("What are we looking for, Sir?")
    if st.button("EXECUTE SEARCH"):
        st.session_state.view = "results"
        st.session_state.last_query = search_input

# MAIN AREA
if st.session_state.view == "results":
    query = st.session_state.last_query
    st.title(f"Market Results: {query.upper()}")
    
    # Simulating a "Scanned" response with options
    cols = st.columns(2)
    
    # Option 1
    with cols[0]:
        st.markdown(f"""
        <div class="product-card">
            <img src="https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?q=80&w=500" style="width:100%; border-radius:8px;">
            <h3>Top Rated {query}</h3>
            <p class="price-tag">$450.00</p>
            <p>Condition: Near Mint<br>Location: Within 5 miles</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("CONTACT SELLER", key="btn1"):
            st.success("Drafting Instagram DM... Redirecting.")
            st.link_button("OPEN INBOX", "https://www.instagram.com/direct/inbox/")

    # Option 2
    with cols[1]:
        st.markdown(f"""
        <div class="product-card">
            <img src="https://images.unsplash.com/photo-1523275335684-37898b6baf30?q=80&w=500" style="width:100%; border-radius:8px;">
            <h3>Budget Choice {query}</h3>
            <p class="price-tag">$290.00</p>
            <p>Condition: Used - Good<br>Location: 12 miles away</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("CONTACT SELLER", key="btn2"):
            # Deep link into marketplace search
            m_url = f"https://www.facebook.com/marketplace/search/?query={urllib.parse.quote(query)}"
            st.link_button("GO TO LISTING", m_url)

    if st.button("RESET HUD"):
        st.session_state.view = "main"
        st.rerun()

else:
    # THE CHAT INTERFACE
    st.title("COMMAND CENTER")
    user_msg = st.chat_input("Ask G.R.E.G. anything...")
    if user_msg:
        st.markdown(f"**YOU:** {user_msg}")
        with st.spinner("G.R.E.G. is thinking..."):
            ans = greg_ai(user_msg)
            st.markdown(f"**G.R.E.G.:** {ans}")