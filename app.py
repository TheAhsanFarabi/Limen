import os
import base64
import json
import streamlit as st
import mimetypes
from huggingface_hub import InferenceClient
from fpdf import FPDF

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="Pond Ecosystem Analyzer 🌿",
    page_icon="🌊",
    layout="wide"
)

# --- Helper: PDF Generator ---
def create_pdf(analysis_text, prompt_type, mode, model_name):
    class PDF(FPDF):
        def header(self):
            self.set_font('Helvetica', 'B', 15)
            self.cell(0, 10, 'Pond Ecosystem Analysis Report', align='C', new_x="LMARGIN", new_y="NEXT")
            self.ln(5)

    pdf = PDF()
    pdf.add_page()
    
    # Metadata
    pdf.set_font("Helvetica", "I", 10)
    
    # 🛡️ SANITIZATION FIX: Encode/Decode metadata to remove emojis
    safe_model = model_name.encode('latin-1', 'replace').decode('latin-1')
    safe_strategy = prompt_type.encode('latin-1', 'replace').decode('latin-1')
    safe_mode = mode.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.cell(0, 10, txt=f"Model: {safe_model}", new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.cell(0, 10, txt=f"Strategy: {safe_strategy} | Mode: {safe_mode}", new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(5)
    
    # Body Content
    pdf.set_font("Helvetica", size=11)
    
    # Sanitization for Body Text
    clean_text = analysis_text.replace("##", "").replace("**", "")
    safe_text = clean_text.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.multi_cell(0, 10, safe_text)
    return bytes(pdf.output())

# --- Sidebar Configuration ---
with st.sidebar:
    # Logo first (From your updated code)
    st.image(
        "https://www.uiu.ac.bd/wp-content/uploads/2023/10/header-logo.png",
        width=150,
        caption=None
    )
    st.header("⚙️ Configuration")
    
    # 1. API Key Input
    st.markdown("### 1. Credentials")
    
    # Link to get token
    st.markdown("[🔑 Get HF API Key](https://huggingface.co/settings/tokens)")
    
    # Persistent Input (Fixed to prevent disappearing on interaction)
    hf_token = st.text_input(
        "Enter Hugging Face Token", 
        type="password", 
        help="Your HF Access Token (Read/Write)"
    )
    
    if hf_token:
        st.success("Token detected! ✅")
    
    st.markdown("---")
    
    # 2. Model Selection
    st.markdown("### 2. AI Model")
    model_id = st.selectbox(
        "Select Vision Model:",
        [
            "Qwen/Qwen3-VL-8B-Instruct",
            "Qwen/Qwen2.5-VL-72B-Instruct", 
            "Qwen/Qwen2-VL-7B-Instruct", 
            "meta-llama/Llama-3.2-11B-Vision-Instruct"
        ],
        index=0,
        help="Select the AI model architecture to use for analysis."
    )

    # 3. Focus Area (Strategy)
    st.markdown("### 3. Focus Area")
    prompt_type = st.selectbox(
        "Strategy:",
        [
            "General Health Check",
            "Water Quality & Turbidity", 
            "Vegetation & Algae Control",
            "Biodiversity & Wildlife Potential"
        ]
    )
    
    st.markdown("---")
    
    # 4. Tips
    st.info("💡 **Tip:** 'Fast Mode' uses strict JSON parsing for metrics. If it fails, try 'Research Mode' for a raw text analysis.")

# --- Define Prompts ---

# Research Mode Prompts (Textual) - UPDATED to 200 words constraint
research_prompts = {
    "General Health Check": 
        "Analyze the overall environment. Format as: '## 1. Visual Observations' and '## 2. Recommended Solutions'. Provide visual cues info and solutions in max 200 words.",
    "Water Quality & Turbidity": 
        "Focus on water quality (turbidity, color). Format as: '## 1. Visual Observations' and '## 2. Recommended Solutions'. Provide visual cues info and solutions in max 200 words.",
    "Vegetation & Algae Control": 
        "Focus on flora. Format as: '## 1. Visual Observations' and '## 2. Recommended Solutions'. Provide visual cues info and solutions in max 200 words.",
    "Biodiversity & Wildlife Potential":
        "Focus on fauna support. Format as: '## 1. Visual Observations' and '## 2. Recommended Solutions'. Provide visual cues info and solutions in max 200 words."
}

# Fast Mode Prompt (JSON extraction)
fast_mode_prompt = (
    "Analyze this pond image and output ONLY a valid JSON object. Do not write any conversational text. "
    "The JSON must have these exact keys: "
    "'clarity_score' (integer 0-100, where 100 is crystal clear), "
    "'algae_risk_score' (integer 0-100, where 100 is dangerous bloom), "
    "'biodiversity_score' (integer 0-100), "
    "'key_observation' (string, max 15 words), "
    "'primary_recommendation' (string, max 15 words). "
)

# --- Main App Interface ---
# Hero Section (Preserved from your code)
st.markdown(
    """
    <style>
        .hero-container {
            text-align: center;
            padding: 2rem 0;
            margin-bottom: 2rem;
        }
        .sdg-badges {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 1rem;
        }
        .sdg-img {
            width: 60px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .sdg-img:hover {
            transform: scale(1.1);
        }
        .hero-title {
            font-size: 3rem;
            font-weight: 800;
            margin: 0;
            background: -webkit-linear-gradient(45deg, #007CF0, #00DFD8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hero-subtitle {
            color: #666;
            font-size: 1.2rem;
            margin-top: 10px;
            font-weight: 500;
        }
        .hero-desc {
            color: #555;
            font-size: 1rem;
            max-width: 700px;
            margin: 15px auto;
            line-height: 1.6;
        }
        /* Card Grid System */
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 30px;
            text-align: left;
        }
        .feature-card {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            border-color: #007CF0;
        }
        .card-icon {
            font-size: 1.8rem;
            margin-bottom: 10px;
            display: block;
        }
        .card-title {
            font-weight: 700;
            color: #333;
            margin-bottom: 5px;
            display: block;
        }
        .card-text {
            font-size: 0.9rem;
            color: #666;
            margin: 0;
        }
        /* Dark mode adjustment for Streamlit */
        @media (prefers-color-scheme: dark) {
            .feature-card {
                background-color: #262730;
                border-color: #444;
            }
            .card-title { color: #fff; }
            .card-text { color: #ccc; }
            .hero-desc { color: #ccc; }
            .hero-subtitle { color: #aaa; }
        }
        .cta-text {
            margin-top: 30px;
            font-weight: 700;
            color: #333;
            font-size: 1.1rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
    </style>

    <div class="hero-container">
        <!-- SDG Badges -->
        <div class="sdg-badges">
            <img src="https://upload.wikimedia.org/wikipedia/commons/8/87/Sustainable_Development_Goal_6.png" class="sdg-img" title="Clean Water and Sanitation">
            <img src="https://upload.wikimedia.org/wikipedia/commons/6/63/Sustainable_Development_Goal_14.png" class="sdg-img" title="Life Below Water">
        </div>

        <!-- Title Section -->
        <h1 class="hero-title">Pond Ecosystem Analyzer</h1>
        <p class="hero-subtitle">AI-Powered Aquatic Intelligence System</p>
        <p class="hero-desc">
            Secure the health of your water bodies with instant AI diagnostics. 
            Monitor turbidity, algae risks, and biodiversity with a single upload.
        </p>

        <!-- Feature Cards -->
        <div class="feature-grid">
            <div class="feature-card">
                <span class="card-icon">📊</span>
                <span class="card-title">Instant Metrics</span>
                <p class="card-text">Get real-time scores for water clarity, algae risk, and biodiversity health.</p>
            </div>
            <div class="feature-card">
                <span class="card-icon">🔬</span>
                <span class="card-title">Deep Research</span>
                <p class="card-text">Receive detailed botanical and ecological insights powered by Vision AI.</p>
            </div>
            <div class="feature-card">
                <span class="card-icon">📥</span>
                <span class="card-title">PDF Export</span>
                <p class="card-text">Generate and download professional PDF reports for record-keeping.</p>
            </div>
            <div class="feature-card">
                <span class="card-icon">🔗</span>
                <span class="card-title">Flexible Input</span>
                <p class="card-text">Analyze via direct file upload or simply paste a valid image URL.</p>
            </div>
        </div>

        <p class="cta-text">⬇️ Start by uploading a pond image below ⬇️</p>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Logic Gate ---
if not hf_token:
    st.info("👋 Welcome! Please enter your Hugging Face API Key in the sidebar to start.")
    st.stop()

# --- Input Section ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📸 Input Source")
    input_type = st.radio("", ["Upload Image", "Image URL"], horizontal=True, label_visibility="collapsed")
    
    image_data = None
    display_image = None
    
    if input_type == "Upload Image":
        uploaded = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])
        if uploaded:
            image_data = uploaded.read()
            mime = uploaded.type
            # Create Data URI
            b64 = base64.b64encode(image_data).decode()
            display_image = f"data:{mime};base64,{b64}"
            st.image(image_data, use_column_width=True, caption="Analysis Target")
            
    else:
        url = st.text_input("Paste URL")
        if url:
            display_image = url
            st.image(url, use_column_width=True, caption="Analysis Target")

with col2:
    st.subheader("📊 Analysis Configuration")
    
    # Mode Selection (Moved to Main Area)
    analysis_mode = st.radio(
        "Select Analysis Mode:",
        ["🚀 Fast Mode (Metrics)", "🔬 Research Mode (Detailed)"],
        captions=["Visual scores & quick stats", "In-depth academic textual analysis"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if st.button("Run Analysis", type="primary", use_container_width=True):
        if not display_image:
            st.error("Please provide an image.")
        else:
            with st.spinner(f"Processing with {model_id}..."):
                try:
                    client = InferenceClient(api_key=hf_token)
                    messages = []
                    
                    # Add Image
                    messages.append({"type": "image_url", "image_url": {"url": display_image}})
                    
                    # Select Prompt based on Mode
                    if "Fast Mode" in analysis_mode:
                        final_prompt = fast_mode_prompt
                    else:
                        final_prompt = research_prompts[prompt_type]
                        
                    messages.append({"type": "text", "text": final_prompt})
                    
                    # API Call
                    completion = client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "user", "content": messages}],
                        max_tokens=500
                    )
                    
                    raw_result = completion.choices[0].message.content
                    st.session_state['result'] = raw_result
                    st.session_state['mode'] = analysis_mode
                    
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- Result Display Logic ---
    if 'result' in st.session_state:
        result = st.session_state['result']
        mode = st.session_state['mode']
        
        st.markdown("### 📝 Results")
        
        # 🚀 Display for FAST MODE (JSON Parsing)
        if "Fast Mode" in mode:
            try:
                # Clean code blocks if LLM adds them
                clean_json = result.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_json)
                
                # Metric Columns
                m1, m2, m3 = st.columns(3)
                m1.metric("Clarity", f"{data.get('clarity_score', 0)}%")
                m2.metric("Algae Risk", f"{data.get('algae_risk_score', 0)}%")
                m3.metric("Biodiversity", f"{data.get('biodiversity_score', 0)}%")
                
                # Progress Bars
                st.caption("Water Clarity Level")
                st.progress(data.get('clarity_score', 0) / 100)
                
                st.caption("Algae Bloom Risk")
                st.progress(data.get('algae_risk_score', 0) / 100)
                
                # Key Takeaways
                st.success(f"**Observation:** {data.get('key_observation', 'N/A')}")
                st.info(f"**Action:** {data.get('primary_recommendation', 'N/A')}")
                
            except json.JSONDecodeError:
                st.warning("Could not parse metrics. Showing raw text instead.")
                st.write(result)
                
        # 🔬 Display for RESEARCH MODE (Text)
        else:
            st.markdown(result)
        
        # Download Button
        st.markdown("---")
        pdf_bytes = create_pdf(str(result), prompt_type, mode, model_id)
        st.download_button("📥 Download Report (PDF)", pdf_bytes, "report.pdf", "application/pdf", use_container_width=True)
