import streamlit as st
import pandas as pd
import pickle

# ==========================
# 1. CYBERPUNK CONFIG
# ==========================
st.set_page_config(
    page_title="NEURAL_GENE_V1",
    page_icon="☣️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load the model
with open('gene_model.pkl', 'rb') as f:
    model_data = pickle.load(f)
model = model_data['model']
model_columns = model_data['model_columns']

# ==========================
# 2. INJECT CUSTOM CSS (THEME)
# ==========================
st.markdown("""
<style>
    /* 1. Main Background */
    .stApp {
        background-color: #050505;
        background-image: linear-gradient(0deg, transparent 24%, rgba(0, 255, 65, .03) 25%, rgba(0, 255, 65, .03) 26%, transparent 27%, transparent 74%, rgba(0, 255, 65, .03) 75%, rgba(0, 255, 65, .03) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(0, 255, 65, .03) 25%, rgba(0, 255, 65, .03) 26%, transparent 27%, transparent 74%, rgba(0, 255, 65, .03) 75%, rgba(0, 255, 65, .03) 76%, transparent 77%, transparent);
        background-size: 50px 50px;
    }

    /* 2. Fonts */
    * {
        font-family: 'Courier New', Courier, monospace !important;
        color: #e0e0e0;
    }

    /* 3. Headers */
    h1, h2, h3 {
        color: #00ff41 !important; /* Matrix Green */
        text-shadow: 0 0 10px #00ff41;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* 4. Text Input Area */
    .stTextArea textarea {
        background-color: #0a0a0a;
        color: #00ff41;
        border: 1px solid #00ff41;
        box-shadow: 0 0 5px #00ff41;
        border-radius: 0px;
    }
    .stTextArea textarea:focus {
        box-shadow: 0 0 15px #00ff41;
        border: 1px solid #fff;
    }

    /* 5. Buttons */
    div.stButton > button {
        background-color: #000;
        color: #ff00ff; /* Neon Pink */
        border: 1px solid #ff00ff;
        border-radius: 0px;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.3s;
        text-transform: uppercase;
    }
    div.stButton > button:hover {
        background-color: #ff00ff;
        color: #000;
        box-shadow: 0 0 20px #ff00ff;
        border: 1px solid #fff;
    }

    /* 6. Sidebar */
    [data-testid="stSidebar"] {
        background-color: #000000;
        border-right: 1px solid #333;
    }

    /* 7. Success/Error Boxes */
    .stSuccess {
        background-color: rgba(0, 255, 65, 0.1);
        border-left: 5px solid #00ff41;
        color: #00ff41;
    }
    .stError {
        background-color: rgba(255, 0, 60, 0.1);
        border-left: 5px solid #ff003c;
        color: #ff003c;
    }
    
    /* 8. Glitch Effect Helper */
    .glitch {
        font-size: 3rem;
        font-weight: bold;
        text-transform: uppercase;
        position: relative;
        text-shadow: 0.05em 0 0 #00fffc, -0.03em -0.04em 0 #fc00ff,
        0.025em 0.04em 0 #fffc00;
        animation: glitch 725ms infinite;
    }
</style>
""", unsafe_allow_html=True)

# ==========================
# 3. SIDEBAR (SYSTEM STATUS)
# ==========================
with st.sidebar:
    st.markdown("## 🖥️ SYSTEM_STATUS")
    st.code("""
> CONNECTED: TRUE
> ENCRYPTION: 256-BIT
> MODEL: MLP_NEURAL_NET
> CPU_USAGE: 12%
> Developer: Miyulas Bandara
    """, language="bash")
    
    st.markdown("---")
    st.markdown("### 🛠️ PROTOCOLS")
    st.write(">> INJECT_DNA_SEQUENCE")
    st.write(">> DECODE_PROMOTER")
    st.write(">> EXECUTE_PREDICTION")
    
    st.markdown("---")
    st.caption("v1.0.4 // NETRUNNER_EDITION")

# ==========================
# 4. MAIN INTERFACE
# ==========================
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown('<div class="glitch">GENE_DECODER_AI</div>', unsafe_allow_html=True)
    st.markdown("**// BIOLOGICAL SEQUENCE ANALYSIS PROTOCOL**")

st.markdown("---")

# Input Section with "Terminal" vibe
st.markdown("### >> INPUT_SEQUENCE_DATA:")
sequence_input = st.text_area("", height=150, placeholder="[PASTE 57-BASE DNA STRING HERE]...")

# Processing Logic (Same as before)
def process_input(sequence):
    sequence = sequence.replace('\n', '').replace(' ', '').lower()
    if len(sequence) != 57:
        return None, f"⚠️ SYSTEM ALERT: LENGTH_MISMATCH [{len(sequence)}/57]"
    valid_bases = set('atcg')
    if not set(sequence).issubset(valid_bases):
         return None, "⚠️ SYSTEM ALERT: CORRUPT_DATA_DETECTED [INVALID CHARS]"
    
    seq_list = list(sequence)
    input_df = pd.DataFrame([seq_list], columns=[f'p{i+1}' for i in range(57)])
    input_encoded = pd.get_dummies(input_df)
    input_encoded = input_encoded.reindex(columns=model_columns, fill_value=0)
    return input_encoded, ""

# Action
st.markdown("<br>", unsafe_allow_html=True)
if st.button("RUN_DIAGNOSTICS [EXECUTE]"):
    if sequence_input:
        with st.spinner("PROCESSING NEURAL TENSORS..."):
            processed_data, error = process_input(sequence_input)
            
            if error:
                st.error(error)
            else:
                prediction = model.predict(processed_data)
                probability = model.predict_proba(processed_data)
                
                st.markdown("---")
                
                # Results Display
                c1, c2 = st.columns(2)
                
                with c1:
                    st.markdown("### >> ANALYSIS_RESULT")
                    if prediction[0] == 1:
                        st.success(f"✅ TARGET_IDENTIFIED: PROMOTER")
                        st.markdown(f"**CONFIDENCE_LEVEL:** `{probability[0][1]*100:.2f}%`")
                    else:
                        st.error(f"❌ TARGET_REJECTED: NON-PROMOTER")
                        st.markdown(f"**CONFIDENCE_LEVEL:** `{probability[0][0]*100:.2f}%`")
                
                with c2:
                    st.markdown("### >> DATA_LOG")
                    st.code(f"""
TIMESTAMP: NOW
ID: {sequence_input[:5]}...
SCAN_COMPLETE: TRUE
                    """)
    else:
        st.warning("⚠️ WAITING FOR INPUT...")