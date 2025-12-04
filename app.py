import os
import base64
import streamlit as st
import mimetypes
from huggingface_hub import InferenceClient

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="Pond Analyzer 🌿",
    page_icon="🌊",
    layout="centered"
)

# --- Helper: Clear Function ---
def clear_app():
    # Delete specific keys from session state to reset widgets
    if "uploaded_file" in st.session_state:
        del st.session_state["uploaded_file"]
    if "url_input" in st.session_state:
        del st.session_state["url_input"]
    if "hf_token" in st.session_state:
        del st.session_state["hf_token"]
    # Rerun the app to refresh the UI
    st.rerun()

# --- Header ---
st.title("🌊 Pond Visual Analyzer")
st.markdown("Analyze pond environments using AI. Select a prompt strategy below.")

# --- 1. User API Key ---
hf_token = st.text_input("Enter your Hugging Face API Key", type="password", key="hf_token")

# --- 2. Prompt Selection (3 Options) ---
prompt_type = st.selectbox(
    "Select Analysis Focus:",
    [
        "Option 1: General Health & Overall Check",
        "Option 2: Water Quality & Turbidity Focus", 
        "Option 3: Vegetation & Algae Control"
    ]
)

# Define the prompts based on selection
prompts = {
    "Option 1: General Health & Overall Check": 
        "Analyze the overall environment of the pond shown. "
        "Strictly format your response into two distinct sections with these headers: "
        "'## 1. Visual Observations' (describe the water color, banks, and surroundings) and "
        "'## 2. Recommended Solutions' (general maintenance and improvement tips). "
        "Keep the language English and professional.",

    "Option 2: Water Quality & Turbidity Focus": 
        "Focus specifically on the water quality indicators such as color, turbidity, and surface debris. "
        "Strictly format your response into two distinct sections with these headers: "
        "'## 1. Visual Observations' (what indicates poor or good water quality) and "
        "'## 2. Recommended Solutions' (filtration, chemical treatments, or natural cleaning methods). "
        "Keep the language English and professional.",

    "Option 3: Vegetation & Algae Control": 
        "Focus on the biological aspects like algae bloom, weeds, and bank plants. "
        "Strictly format your response into two distinct sections with these headers: "
        "'## 1. Visual Observations' (identify visible plants or algae types) and "
        "'## 2. Recommended Solutions' (how to manage overgrowth or plant beneficial species). "
        "Keep the language English and professional."
}

selected_prompt = prompts[prompt_type]

# --- 3. Image Input ---
input_option = st.radio("Select Input Method:", ["Upload Image", "Paste Image URL"])

image_bytes = None
image_url = None
image_mime_type = None

if input_option == "Upload Image":
    # added key="uploaded_file" so we can clear it later
    uploaded_file = st.file_uploader("Choose an image...", type=["png", "jpg", "jpeg"], key="uploaded_file")
    if uploaded_file:
        image_bytes = uploaded_file.read()
        image_mime_type = uploaded_file.type
        st.image(image_bytes, caption="Uploaded Image", use_column_width=True)
elif input_option == "Paste Image URL":
    # added key="url_input" so we can clear it later
    image_url = st.text_input("Enter Image URL", key="url_input")
    if image_url:
        st.image(image_url, caption="Image from URL", use_column_width=True)

# --- 4. Action Buttons (Columns for layout) ---
col1, col2 = st.columns([1, 1])

with col1:
    analyze_btn = st.button("Analyze Image", type="primary", use_container_width=True)

with col2:
    clear_btn = st.button("Clear All", on_click=clear_app, use_container_width=True)

# --- 5. Analysis Logic ---
if analyze_btn:
    if not hf_token:
        st.error("API Key is required!")
    elif not (image_bytes or image_url):
        st.error("Please provide an image!")
    else:
        st.info(f"Analyzing with strategy: {prompt_type}...")
        
        try:
            client = InferenceClient(api_key=hf_token)
            msg_content = []
            
            # Handle Image Logic
            if image_url:
                msg_content.append({"type": "image_url", "image_url": {"url": image_url}})
            elif image_bytes:
                b64_image = base64.b64encode(image_bytes).decode("utf-8")
                data_uri = f"data:{image_mime_type};base64,{b64_image}"
                msg_content.append({"type": "image_url", "image_url": {"url": data_uri}})

            # Add the selected prompt
            msg_content.append({"type": "text", "text": selected_prompt})

            # API Call
            completion = client.chat.completions.create(
                model="Qwen/Qwen3-VL-8B-Instruct",
                messages=[{"role": "user", "content": msg_content}]
            )
            
            response_text = completion.choices[0].message.content
            
            st.success("Analysis Complete ✅")
            st.markdown("---")
            
            # The model is instructed to include Markdown headers, so we can just render it directly
            st.markdown(response_text)
            
        except Exception as e:
            st.error(f"API call failed: {e}")
