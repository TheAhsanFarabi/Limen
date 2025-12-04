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
    pdf.cell(0, 10, txt=f"Model: {model_name}", new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.cell(0, 10, txt=f"Strategy: {prompt_type} | Mode: {mode}", new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(5)
    
    # Body Content
    pdf.set_font("Helvetica", size=11)
    
    # Sanitization for PDF
    clean_text = analysis_text.replace("##", "").replace("**", "")
    safe_text = clean_text.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.multi_cell(0, 10, safe_text)
    return bytes(pdf.output())

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # 1. API Key Input
    st.markdown("### 1. Credentials")
    hf_token = st.text_input("Enter Hugging Face Token", type="password", help="Your HF Access Token")
    st.link_button("🔑 Get HF API Key", "https://huggingface.co/settings/tokens")
    
    st.markdown("---")
    
    # 2. Model Selection (Restored)
    st.markdown("### 2. AI Model")
    model_id = st.selectbox(
        "Select Vision Model:",
        [
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
    
    # 4. Tips (Restored)
    st.info("💡 **Tip:** 'Fast Mode' uses strict JSON parsing for metrics. If it fails, try 'Research Mode' for a raw text analysis.")

# --- Define Prompts ---

# Research Mode Prompts (Textual)
research_prompts = {
    "General Health Check": 
        "Analyze the overall environment. Format as: '## 1. Visual Observations' and '## 2. Scientific Recommendations'. Be detailed and academic.",
    "Water Quality & Turbidity": 
        "Focus on water quality (turbidity, color). Format as: '## 1. Visual Observations' and '## 2. Remediation Protocols'. Be detailed and academic.",
    "Vegetation & Algae Control": 
        "Focus on flora. Format as: '## 1. Botanical Identification' and '## 2. Management Strategy'. Be detailed and academic.",
    "Biodiversity & Wildlife Potential":
        "Focus on fauna support. Format as: '## 1. Habitat Assessment' and '## 2. Ecological Enhancement'. Be detailed and academic."
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

# Hero Section (Cleaned up - No University Icon)
st.markdown(
    """
    <div style='text-align: center; padding: 2rem 0; margin-bottom: 2rem;'>
        <div style='display: flex; justify_content: center; align-items: center; gap: 15px; margin-bottom: 1rem;'>
            <img src="https://upload.wikimedia.org/wikipedia/commons/8/87/Sustainable_Development_Goal_6.png" width="50" style="border-radius: 10px;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/6/63/Sustainable_Development_Goal_14.png" width="50" style="border-radius: 10px;">
        </div>
        <h1 style='margin:0; font-size: 2.8rem;'>🌊 Pond Ecosystem Analyzer</h1>
        <p style='color: #666; margin-top: 5px; font-size: 1.1rem;'>AI-Powered Aquatic Intelligence System</p>
    </div>
    """, unsafe_allow_html=True
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
