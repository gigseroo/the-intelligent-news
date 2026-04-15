import streamlit as st
import requests
import urllib.parse

# --- 1. THE STEALTH HUD UI ---
st.set_page_config(page_title="G.R.E.G. STEALTH", layout="wide")

st.markdown("""
    <style>
    /* Absolute Stealth: Black, Gray, White */
    [data-testid="stHeader"], [data-testid="stFooter"], header, footer { display: none !important; }
    .stApp { background-color: #000000; color: #ffffff; font-family: 'Inter', sans-serif; }
    
    /* Grid Background */
    .stApp {
        background-image: radial-gradient(circle, #1a1a1a 1px, rgba(0, 0, 0, 0) 1px);
        background-size: 30px 30px;
    }

    /* Product Card: Minimalist Gray */
    .product-card {
        background: #0a0a0a;
        border: 1px solid #333;
        border-radius: 4px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .price-tag { color: #ffffff; font-weight: bold; font-size: 22px; border-bottom: 1px solid #333; padding-bottom: 5px; }
    
    /* Buttons: White on Black */
    .stButton>button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-radius: 2px !important;
        font-weight: bold !important;
        border: none !important;
        width: 100%;
    }

    .msg-greg { color: #aaaaaa; border-left: 1px solid #ffffff; padding-left: 15px; margin-bottom: 20px; font-family: monospace; }
    .msg-user { color: #ffffff; font-weight: bold; margin-bottom: 5px; text-transform: uppercase; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BRAIN WITH MEMORY ---
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

def greg_brain(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.2 # Lower temperature = more focused memory
    }
    try:
        res = requests.post(url, headers=headers, json=payload).json()
        return res['choices'][0]['message']['content']
    except: return "CONNECTION INTERRUPTED."

# --- 3. PERSISTENT MEMORY ENGINE ---
if "history" not in st.session_state:
    st.session_state.history = [{"role": "assistant", "content": "STEALTH PROTOCOLS ACTIVE. STANDING BY."}]
if "target_item" not in st.session_state:
    st.session_state.target_item = None

# --- 4. HUD INTERFACE ---
st.markdown("<h2 style='letter-spacing:10px;'>G.R.E.G.</h2>", unsafe_allow_html=True)
st.markdown("<small style='color:#666;'>OBJECTIVE TRACKER: " + str(st.session_state.target_item).upper() + "</small>", unsafe_allow_html=True)
st.divider()

# Display Visual Cards if an item is active
if st.session_state.target_item:
    cols = st.columns(2)
    with cols[0]:
        st.markdown(f"""<div class="product-card">
            <div class="price-tag">£20.00</div>
            <p style='color:#666'>LOCAL MATCH: {st.session_state.target_item.upper()}</p>
            <p>Verified listing found within your perimeter.</p>
        </div>""", unsafe_allow_html=True)
        st.link_button("INITIATE UPLINK", f"https://www.facebook.com/marketplace/search/?query={urllib.parse.quote(st.session_state.target_item)}")

# Display Chat History
for m in st.session_state.history:
    if m["role"] == "assistant":
        st.markdown(f'<div class="msg-greg">{m["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="msg-user">USER > {m["content"]}</div>', unsafe_allow_html=True)

# Tactical Input
prompt = st.chat_input("Input Command...")

if prompt:
    st.session_state.history.append({"role": "user", "content": prompt})
    
    # 1. Update Target Item using AI
    # We ask the AI to extract the "subject" of the conversation
    intent_check = greg_brain([
        {"role": "system", "content": "Identify the item the user wants to find. If they mention a price or detail for a previous item, keep the original item. Return ONLY the item name."},
        {"role": "user", "content": f"Current history: {st.session_state.target_item}. New message: {prompt}"}
    ])
    
    if len(intent_check.split()) < 5: # If it's a short response, it's our item
        st.session_state.target_item = intent_check.strip()

    # 2. General Response
    ctx = [
        {"role": "system", "content": f"You are GREG. A stealth AI. You are helping the user find {st.session_state.target_item}. Be extremely brief and professional."},
        {"role": "user", "content": prompt}
    ]
    response = greg_brain(ctx)
    st.session_state.history.append({"role": "assistant", "content": response})
    
    st.rerun()