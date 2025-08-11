import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageOps
import numpy as np
import random, time, os
from rapidfuzz import fuzz
import easyocr

# ----- CONFIG -----
CANVAS_W, CANVAS_H = 900, 300
SAVE_DIR = "handwriting_attempts"
os.makedirs(SAVE_DIR, exist_ok=True)

# EasyOCR reader
reader = easyocr.Reader(['en'], gpu=False)

# Word list
WORDS = ["TRAIN", "APPLE", "HOUSE", "PHONE", "HAPPY", "CHAIR", "PAPER", "MOUSE", "CLOUD", "PLANT", "CODE", "PYTHON"]

st.set_page_config(page_title="Word Game", layout="wide")
st.title("✍ Word Challenge — Draw the word to WIN")

# State
if "target_word" not in st.session_state:
    st.session_state.target_word = random.choice(WORDS)
if "last_result" not in st.session_state:
    st.session_state.last_result = ""
if "canvas_key" not in st.session_state:
    st.session_state.canvas_key = "canvas"

# Word display
colors = ["#FF5733", "#FFC300", "#FF8C00", "#00CC66", "#3399FF", "#FF33A6"]
letter_boxes = ""
for i, letter in enumerate(st.session_state.target_word):
    letter_boxes += (
        f"<span style='background-color:{colors[i % len(colors)]};"
        f"color:white;font-size:40px;text-align:center;"
        f"display:inline-block;margin:2px;padding:10px 14px;"
        f"border-radius:6px;width:50px;line-height:1'>{letter}</span>"
    )
st.markdown(
    f"<div style='text-align:center;margin-bottom:8px;display:inline-flex;gap:0px'>{letter_boxes}</div>",
    unsafe_allow_html=True
)

col_left, col_right = st.columns([3, 1])

with col_right:
    st.subheader("Settings")
    stroke_w = st.slider("Stroke width", 2, 12, 6)
    threshold = st.slider("Match threshold (%)", 30, 100, 80)

with col_left:
    st.markdown("Draw the whole word on the canvas below:")

    # Canvas
    canvas_result = st_canvas(
        fill_color="rgba(255,255,255,1)",
        stroke_width=stroke_w,
        stroke_color="#000000",
        background_color="#FFFFFF",
        height=CANVAS_H,
        width=CANVAS_W,
        drawing_mode="freedraw",
        key=st.session_state.canvas_key,
        update_streamlit=True,
    )

    b1, b2, b3 = st.columns(3)

    # Clear
    with b1:
        if st.button("Clear"):
            st.session_state.canvas_key = f"canvas_{random.randint(0, 9999)}"  # new key forces reset
            st.rerun()

    # Check
    with b2:
        if st.button("Check"):
            if canvas_result is None or canvas_result.image_data is None:
                st.warning("Draw something first.")
            else:
                img = Image.fromarray((canvas_result.image_data[:, :, :3]).astype(np.uint8))
                gray = ImageOps.grayscale(img)
                factor = 2
                big = gray.resize((CANVAS_W * factor, CANVAS_H * factor))
                bw = big.point(lambda x: 0 if x < 200 else 255, '1')

                ts = int(time.time())
                proc_path = os.path.join(SAVE_DIR, f"{ts}_proc.png")
                bw.convert("RGB").save(proc_path)

                result = reader.readtext(proc_path, detail=0)
                ocr_text = "".join(result).strip().upper()

                st.write("Detected (OCR):", f"{ocr_text or '[none]'}")
                score = fuzz.ratio(ocr_text or "", st.session_state.target_word)
                st.write(f"Match score: {score} / 100 (threshold {threshold})")

                if score >= threshold:
                    st.balloons()
                    st.success(f"🏆 WIN — {score}% match!")
                    st.session_state.last_result = f"WIN ({score}%)"
                else:
                    st.error(f"❌ FAIL — {score}% match. Try again.")
                    st.session_state.last_result = f"FAIL ({score}%)"

    # New Word
    with b3:
        if st.button("New Word"):
            st.session_state.target_word = random.choice(WORDS)
            st.session_state.last_result = ""
            st.rerun()

# Show result
if st.session_state.last_result:
    st.markdown(f"### Result: {st.session_state.last_result}")

    @st.cache_resource
    def load_ocr():
        return easyocr.Reader(['en'], gpu=False)
    reader = load_ocr()