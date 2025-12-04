import streamlit as st
from huggingface_hub import InferenceClient
import requests
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="Pond Checker", page_icon="🌿")

st.title("🌿 Pond Visual Analyzer")
st.caption("Upload an image, paste a link, or capture a photo. Then let the VLM judge the vibe.")

# --- API key ---
hf_key = st.text_input("🔑 Enter your HuggingFace API Key:", type="password")
if not hf_key:
    st.warning("API key lagbe bro. Enter it first.")
    st.stop()

client = InferenceClient(api_key=hf_key)

# --- Image input ---
option = st.radio("Pick input method:", ["Image URL", "Upload File", "Camera"])

img = None

if option == "Image URL":
    url = st.text_input("Paste image URL:")
    if url:
        try:
            res = requests.get(url)
            img = Image.open(BytesIO(res.content))
            st.image(img, caption="Your Image")
        except:
            st.error("Bro this URL ain’t loading. Try another one.")

elif option == "Upload File":
    file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    if file:
        img = Image.open(file)
        st.image(img, caption="Your Image")

else:  # Camera
    file = st.camera_input("Take a photo")
    if file:
        img = Image.open(file)
        st.image(img, caption="Your Photo")

# --- Run VLM ---
if st.button("Analyze 🌱"):
    if img is None:
        st.error("Image dite hobe.")
    else:
        # Convert image to bytes
        buf = BytesIO()
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()

        try:
            completion = client.chat.completions.create(
                model="Qwen/Qwen3-VL-8B-Instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe the visual cues of the pond and suggest remedies to improve environmental quality. Write within 100 words. Write in Bangla Language."},
                            {"type": "image", "image": img_bytes}
                        ]
                    }
                ],
            )

            reply = completion.choices[0].message["content"][0]["text"]
            st.success("Analysis Complete!")
            st.write(reply)

        except Exception as e:
            st.error(f"API call failed: {e}")
