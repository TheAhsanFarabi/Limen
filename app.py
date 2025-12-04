import os
import base64
import streamlit as st
import mimetypes # New import for getting the image MIME type
from huggingface_hub import InferenceClient

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="Pond Analyzer 🌿",
    page_icon="🖼️",
    layout="centered"
)

st.title("🌊 Pond Visual Analyzer")
st.markdown(
    """
    Upload an image, paste a link, or capture a photo 📸, 
    and get an environmental analysis with suggested remedies.
    """
)

# --- User API Key ---
hf_token = st.text_input("Enter your Hugging Face API Key", type="password")

# --- Image Input ---
input_option = st.radio("Select Input Method:", ["Upload Image", "Paste Image URL"])

image_bytes = None
image_url = None
image_mime_type = None

if input_option == "Upload Image":
    uploaded_file = st.file_uploader("Choose an image...", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        image_bytes = uploaded_file.read()
        image_mime_type = uploaded_file.type # Get MIME type directly from Streamlit file object
        st.image(image_bytes, caption="Uploaded Image", use_column_width=True)
elif input_option == "Paste Image URL":
    image_url = st.text_input("Enter Image URL")
    if image_url:
        st.image(image_url, caption="Image from URL", use_column_width=True)

# --- Analyze Button ---
if st.button("Analyze"):

    if not hf_token:
        st.error("API Key is required!")
    elif not (image_bytes or image_url):
        st.error("Please provide an image!")
    else:
        st.info("Sending request to Hugging Face Inference API...")
        
        try:
            client = InferenceClient(api_key=hf_token)

            # Prepare the message payload
            msg_content = []
            
            if image_url:
                # For URL, add it directly as a string or a dict with 'url' key, depending on model requirement
                msg_content.append({"type": "image_url", "image_url": {"url": image_url}})
            
            elif image_bytes:
                # 💥 FIX 1: Convert bytes to base64 string and format as a **Data URI**
                b64_image = base64.b64encode(image_bytes).decode("utf-8")
                
                # Construct the Data URI: data:<mime_type>;base64,<base64_string>
                data_uri = f"data:{image_mime_type};base64,{b64_image}"
                
                # Append the image as a URL of type Data URI
                msg_content.append({"type": "image_url", "image_url": {"url": data_uri}})


            # Add the text prompt (must be after the image for multi-modal context)
            msg_content.append(
                {"type": "text", "text": "Describe the visual cues of the pond and suggest remedies to improve the environment. Write in Bangla, max 100 words."}
            )

            completion = client.chat.completions.create(
                model="Qwen/Qwen3-VL-8B-Instruct",
                messages=[{"role": "user", "content": msg_content}]
            )
            
            st.success("Analysis Complete ✅")
            
            # 💥 FIX 2: Correctly extract the text content from the API response object
            response_text = completion.choices[0].message.content
            
            st.write(response_text)
            
        except Exception as e:
            st.error(f"API call failed: {e}")
