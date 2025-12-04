import streamlit as st
from huggingface_hub import InferenceClient
import requests
from io import BytesIO
from PIL import Image
import base64

# ---- Page Config ----
st.set_page_config(
    page_title="Pond VLM Analyzer",
    page_icon="🌿",
    layout="centered",
)

# ---- Main Title ----
st.markdown(
    "<h1 style='text-align:center; font-size:40px;'>🌿 Pond Visual Analyzer</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center; color:gray;'>Check the vibe of your pond and get eco-friendly fixes.</p>",
    unsafe_allow_html=True,
)

# ---- API Key ----
hf_key = st.text_input("🔑 HuggingFace API Key (required)", type="password")

if not hf_key:
    st.info("API key lagbe bro, nahole kichu hobe na.")
    st.stop()

client = InferenceClient(api_key=hf_key)

# ---- Image Input Options ----
st.subheader("📸 Image Input")

method = st.radio(
    "Pick how you wanna give the image:",
    ["Paste Image URL", "Upload Image", "Use Camera"],
    horizontal=True,
)

img = None

if method == "Paste Image URL":
    url = st.text_input("Paste image URL here:")
    if url:
        try:
            res = requests.get(url)
            img = Image.open(BytesIO(res.content))
            st.image(img, caption="📷 Loaded Image", use_column_width=True)
        except:
            st.error("URL kaj korse na bro. Check the link.")

elif method == "Upload Image":
    file = st.file_uploader("Upload JPG / PNG", type=["jpg", "jpeg", "png"])
    if file:
        img = Image.open(file)
        st.image(img, caption="📷 Uploaded Image", use_column_width=True)

else:  # Camera
    file = st.camera_input("Take a photo")
    if file:
        img = Image.open(file)
        st.image(img, caption="📷 Captured Image", use_column_width=True)

# ---- Analyze Button ----
st.markdown("---")
st.subheader("🧠 Analyze")
run = st.button("Analyze 🌱", use_container_width=True)

if run:
    if img is None:
        st.error("Image dite hobe first.")
    else:
        # Convert image to base64
        buf = BytesIO()
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        try:
            result = client.chat.completions.create(
                model="Qwen/Qwen3-VL-8B-Instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Describe the visual cues of the pond and "
                                    "suggest remedies to improve environmental quality. "
                                    "Write within 100 words in Bangla."
                                ),
                            },
                            {"type": "image", "image": img_b64},
                        ],
                    }
                ],
            )

            reply = result.choices[0].message["content"][0]["text"]

            st.success("Analysis Ready 🌿💧")
            st.markdown(
                f"""
                <div style='padding:15px; background:#f0f7f0; border-radius:10px;'>
                {reply}
                </div>
                """,
                unsafe_allow_html=True,
            )

        except Exception as e:
            st.error(f"API call failed: {e}")

# ---- Footer ----
st.markdown(
    "<p style='text-align:center; color:gray; margin-top:30px;'>Built with ❤️ & VLMs</p>",
    unsafe_allow_html=True,
)
