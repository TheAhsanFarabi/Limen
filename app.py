import os
import base64
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

# --- Helper: PDF Generator (Fixed for Unicode/fpdf2) ---
def create_pdf(analysis_text, prompt_type):
    class PDF(FPDF):
        def header(self):
            self.set_font('Helvetica', 'B', 15)
            self.cell(0, 10, 'Pond Ecosystem Analysis Report', align='C', new_x="LMARGIN", new_y="NEXT")
            self.ln(5)

    pdf = PDF()
    pdf.add_page()
    
    # Metadata
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 10, txt=f"Focus Strategy: {prompt_type}", new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(5)
    
    # Body Content
    pdf.set_font("Helvetica", size=11)
    
    # --- 🛡️ THE FIX: Safe Text Sanitization ---
    # Standard PDF fonts (Helvetica) don't support emojis (🌿, 🌊).
    # We strip Markdown (##, **) and replace unsupported characters with '?' 
    # to prevent the app from crashing.
    clean_text = analysis_text.replace("##", "").replace("**", "")
    
    # This line encodes the text to Latin-1 (standard PDF) and replaces 
    # errors (emojis) with a '?' instead of crashing.
    safe_text = clean_text.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.multi_cell(0, 10, safe_text)
    
    # Output the PDF as bytes
    return bytes(pdf.output())

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # 1. API Key Input
    hf_token = st.text_input("Hugging Face API Key", type="password", help="Enter your HF read/write token")
    
    st.markdown("---")
    
    # 2. Model Selection
    model_id = st.selectbox(
        "Select AI Model",
        ["Qwen/Qwen3-VL-8B-Instruct", "meta-llama/Llama-3.2-11B-Vision-Instruct", "Qwen/Qwen2-VL-7B-Instruct"],
        index=0
    )
    
    # 3. Analysis Focus (4 Options)
    prompt_type = st.radio(
        "Analysis Focus Strategy",
        [
            "General Health Check",
            "Water Quality & Turbidity", 
            "Vegetation & Algae Control",
            "Biodiversity & Wildlife Potential"
        ]
    )
    
    st.markdown("---")
    st.info("💡 **Tip:** Use 'General Health' for a broad overview, or specific modes for targeted advice.")

# --- Define Prompts ---
prompts = {
    "General Health Check": 
        "Analyze the overall environment of the pond shown. "
        "Strictly format your response into two distinct sections with these headers: "
        "'## 1. Visual Observations' (describe the water color, banks, and surroundings) and "
        "'## 2. Recommended Solutions' (general maintenance and improvement tips). "
        "Keep the language English and professional.",

    "Water Quality & Turbidity": 
        "Focus specifically on the water quality indicators such as color, turbidity, and surface debris. "
        "Strictly format your response into two distinct sections with these headers: "
        "'## 1. Visual Observations' (what indicates poor or good water quality) and "
        "'## 2. Recommended Solutions' (filtration, chemical treatments, or natural cleaning methods). "
        "Keep the language English and professional.",

    "Vegetation & Algae Control": 
        "Focus on the biological aspects like algae bloom, weeds, and bank plants. "
        "Strictly format your response into two distinct sections with these headers: "
        "'## 1. Visual Observations' (identify visible plants or algae types) and "
        "'## 2. Recommended Solutions' (how to manage overgrowth or plant beneficial species). "
        "Keep the language English and professional.",
        
    "Biodiversity & Wildlife Potential":
        "Analyze the pond's potential to support fish, amphibians, and birds. "
        "Strictly format your response into two distinct sections with these headers: "
        "'## 1. Visual Observations' (habitats, shelter, water depth cues) and "
        "'## 2. Recommended Solutions' (adding logs, specific plants, or depth variation to encourage wildlife). "
        "Keep the language English and professional."
}

# --- Main App Interface ---

# Hero Section
st.markdown(
    """
    <div style='text-align: center; padding: 2rem 0;'>
        <h1>🌊 Pond Ecosystem Analyzer</h1>
        <p style='font-size: 1.2rem; color: #666;'>
            Advanced AI diagnostics for aquatic environments. <br>
            Upload a photo to detect water quality issues, algae blooms, and ecological imbalances.
        </p>
    </div>
    """, unsafe_allow_html=True
)

# --- Logic Gate: Check for API Key ---
if not hf_token:
    st.warning("🔒 Please enter your Hugging Face API Key in the sidebar to unlock the analyzer.")
    st.stop()

# --- Image Input Section ---
col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    st.subheader("1. Input Data")
    input_option = st.radio("Choose Input Method:", ["Upload Image", "Paste Image URL"], horizontal=True)

    image_bytes = None
    image_url = None
    image_mime_type = None

    if input_option == "Upload Image":
        uploaded_file = st.file_uploader("Upload pond image", type=["png", "jpg", "jpeg"])
        if uploaded_file:
            image_bytes = uploaded_file.read()
            image_mime_type = uploaded_file.type
            st.image(image_bytes, caption="Preview", use_column_width=True, channels="RGB")
            
    elif input_option == "Paste Image URL":
        image_url = st.text_input("Enter Image URL")
        if image_url:
            st.image(image_url, caption="Preview", use_column_width=True)

with col2:
    st.subheader("2. AI Analysis")
    
    # Placeholders for results
    result_container = st.empty()
    
    # Analyze Button
    if st.button("🔍 Run Analysis", type="primary", use_container_width=True):
        if not (image_bytes or image_url):
            st.error("⚠️ Please provide an image first.")
        else:
            with st.spinner(f"Analyzing for {prompt_type}..."):
                try:
                    client = InferenceClient(api_key=hf_token)
                    msg_content = []
                    
                    # Image Logic
                    if image_url:
                        msg_content.append({"type": "image_url", "image_url": {"url": image_url}})
                    elif image_bytes:
                        b64_image = base64.b64encode(image_bytes).decode("utf-8")
                        data_uri = f"data:{image_mime_type};base64,{b64_image}"
                        msg_content.append({"type": "image_url", "image_url": {"url": data_uri}})

                    # Text Prompt
                    msg_content.append({"type": "text", "text": prompts[prompt_type]})

                    # API Call
                    completion = client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "user", "content": msg_content}],
                        max_tokens=500
                    )
                    
                    response_text = completion.choices[0].message.content
                    
                    # Store result in session state
                    st.session_state['last_analysis'] = response_text
                    
                    # Display Result
                    result_container.markdown(response_text)
                    
                except Exception as e:
                    st.error(f"Analysis Failed: {str(e)}")

    # Show Download Button if analysis exists
    if 'last_analysis' in st.session_state:
        # Re-display the analysis so it doesn't disappear on interaction
        result_container.markdown(st.session_state['last_analysis'])
        
        st.markdown("---")
        # Generate PDF with Safe Text Logic
        pdf_data = create_pdf(st.session_state['last_analysis'], prompt_type)
        
        st.download_button(
            label="📄 Download Report as PDF",
            data=pdf_data,
            file_name="pond_analysis_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
