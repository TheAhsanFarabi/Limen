import os
import base64
import streamlit as st
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

if input_option == "Upload Image":
    uploaded_file = st.file_uploader("Choose an image...", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        image_bytes = uploaded_file.read()
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
        client = InferenceClient(api_key=hf_token)

        # Prepare the message payload
        msg_content = [
            {"type": "text", "text": "Describe the visual cues of the pond and suggest remedies to improve the environment. Write in Bangla, max 100 words."}
        ]

        if image_url:
            msg_content.append({"type": "image_url", "image_url": {"url": image_url}})
        elif image_bytes:
            # Convert bytes to base64 string for JSON
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            msg_content.append({"type": "image_base64", "image_base64": b64_image})

        try:
            completion = client.chat.completions.create(
                model="Qwen/Qwen3-VL-8B-Instruct",
                messages=[{"role": "user", "content": msg_content}]
            )
            st.success("Analysis Complete ✅")
            st.write(completion.choices[0].message["content"][0]["text"])
        except Exception as e:
            st.error(f"API call failed: {e}")
