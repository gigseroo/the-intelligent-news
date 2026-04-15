import streamlit as st
import requests
import urllib.parse

# --- 1. G.R.E.G. STEALTH UI ---
st.set_page_config(page_title="G.R.E.G.", layout="wide")

st.markdown("""
    <style>
    /* Kill Streamlit UI Elements */
    [data-testid="stHeader"], [data-testid="stFooter"], header, footer { display: none !important; }
    .stApp { background-color: #050505; color: #00d2ff; }
    
    /* G.R.E.G. Core Visual */
    .greg-orb {
        width: 100px; height: 100px;
        border: 2px solid #00d2ff;
        border-radius: 50%;
        margin: 10px auto;
        box-shadow: 0 0 20px #00d2ff, inset 0 0 10px #00d2ff;
        display: flex; align-items: center; justify-content: center;
        font-family: 'Share Tech Mono', monospace;
        letter-spacing: 2px;
        animation: pulse 3s ease-in-out infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); opacity: 0.7; }
        50% { transform: scale(1.05); opacity: 1; box-shadow: 0 0 40px #00d2ff; }
        100% { transform: scale(1); opacity: 0.7; }
    }

    /* Conversation Bubbles */
    .greg-response {
        background: rgba(0, 210, 255, 0.08);
        border-left: 3px solid #00d2ff;
        padding: 15px; border-radius: 5px;
        margin: 10px 0; font-family: monospace;
    }
    .user-entry {
        background: #111;
        padding: 10px; border-radius: 5px;
        margin: 10px 0 10px auto; width: fit-content;
        max-width: 80%; border: 1px solid #333;
        color: #fff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE BRAIN ---
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

def greg_brain(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.5
    }
    try:
        res = requests.post(url, headers=headers, json=payload).json()
        return res['choices'][0]['message']['content']
    except: return "Neural link unstable. Standing by."

# --- 3. SYSTEM STATE ---
if "greg_history" not in st.session_state:
    st.session_state.greg_history = [{"role": "assistant", "content": "System Online. How can I assist you, Sir?"}]

# --- 4. MAIN INTERFACE ---
st.markdown('<div class="greg-orb">GREG</div>', unsafe_allow_html=True)

# Display Conversation History
for chat in st.session_state.greg_history:
    if chat["role"] == "assistant":
        st.markdown(f"<div class='greg-response'>{chat['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='user-entry'>{chat['content']}</div>", unsafe_allow_html=True)

# Fixed Input at Bottom
prompt = st.chat_input("Command G.R.E.G...")

if prompt:
    # 1. Add user message to history
    st.session_state.greg_history.append({"role": "user", "content": prompt})
    
    cmd_lower = prompt.lower()
    
    # 2. Logic Layer: Automated Actions
    if "marketplace" in cmd_lower:
        item = cmd_lower.replace("search marketplace for", "").replace("search", "").strip()
        url = f"https://www.facebook.com/marketplace/search/?query={urllib.parse.quote(item)}"
        ans = f"Scanning Facebook Marketplace for '{item.upper()}'. Uplink ready below."
        st.session_state.greg_history.append({"role": "assistant", "content": ans})
        st.link_button("EXECUTE MARKETPLACE LINK", url)
        
    elif "instagram" in cmd_lower or "message" in cmd_lower:
        ans = "Redirecting to Instagram Neural Net. Inbox access granted."
        st.session_state.greg_history.append({"role": "assistant", "content": ans})
        st.link_button("EXECUTE INSTAGRAM LINK", "https://www.instagram.com/direct/inbox/")
        
    else:
        # 3. Brain Layer: General Conversation
        with st.spinner("Processing..."):
            context = [{"role": "system", "content": "You are GREG. Be efficient, tech-focused, and call the user Sir."}]
            context.extend(st.session_state.greg_history[-5:]) # Give GREG memory of last 5 messages
            response = greg_brain(context)
            st.session_state.greg_history.append({"role": "assistant", "content": response})
    
    st.rerun()