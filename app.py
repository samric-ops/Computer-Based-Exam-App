import streamlit as st
import json
import pandas as pd
import os
import time
from datetime import datetime, timedelta
import fitz
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="Computer-Based Exam", layout="wide")

PDF_PATH = "/tmp/exam.pdf"
JSON_PATH = "/tmp/exam_questions.json"

default_session = {
    "answers": {}, "submitted": False, "start_time": None,
    "timer_running": False, "score": None, "feedback": {}, "questions": None
}
for key, value in default_session.items():
    if key not in st.session_state:
        st.session_state[key] = value

st.sidebar.header("🛠️ Admin Panel")
admin_password = st.sidebar.text_input("🔑 Admin Password", type="password")
CORRECT_PASSWORD = "exam2024"

if admin_password == CORRECT_PASSWORD:
    st.sidebar.success("✅ Admin mode")
    uploaded_pdf = st.sidebar.file_uploader("📄 Upload PDF", type=["pdf"])
    uploaded_json = st.sidebar.file_uploader("📊 Upload JSON", type=["json"])

    if st.sidebar.button("📤 Set as Current Exam"):
        if uploaded_pdf:
            with open(PDF_PATH, "wb") as f:
                f.write(uploaded_pdf.getvalue())
        if uploaded_json:
            with open(JSON_PATH, "wb") as f:
                f.write(uploaded_json.getvalue())
        st.rerun()

    if st.sidebar.button("🗑️ Clear Exam"):
        for p in [PDF_PATH, JSON_PATH]:
            if os.path.exists(p): os.remove(p)
        st.rerun()

    # Debug viewer
    with st.sidebar.expander("🔍 JSON Debug", expanded=True):
        if os.path.exists(JSON_PATH):
            with open(JSON_PATH, "rb") as f:
                raw_bytes = f.read()[:500]
            st.write("First 500 bytes:", raw_bytes)
            try:
                data = json.loads(raw_bytes)
                st.write("Parsed JSON type:", type(data))
                if isinstance(data, list):
                    st.write(f"List length: {len(data)}")
                elif isinstance(data, dict):
                    st.write("Dict keys:", list(data.keys()))
                else:
                    st.write("Unexpected type")
            except Exception as e:
                st.write("Parse error:", e)
        else:
            st.write("No JSON file.")
else:
    st.sidebar.info("Enter password.")

# Load files
pdf_bytes = None
questions = None
if os.path.exists(PDF_PATH):
    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

if os.path.exists(JSON_PATH):
    try:
        with open(JSON_PATH, "r", encoding='utf-8') as f:
            raw = json.load(f)
        if isinstance(raw, list):
            questions = raw
        elif isinstance(raw, dict):
            # Look for any list value
            for v in raw.values():
                if isinstance(v, list):
                    questions = v
                    break
            if questions is None:
                st.error("JSON is a dict but contains no list. Please use a list of questions.")
        else:
            st.error("JSON is neither list nor dict.")
    except Exception as e:
        st.error(f"JSON parse error: {e}")

# Timer & zoom
timer_minutes = st.sidebar.number_input("Duration (min)", 1, 180, 60)
if pdf_bytes:
    zoom = st.sidebar.slider("Zoom", 2.0, 5.0, 3.0, 0.2)

st.title("📝 Computer-Based Exam")

if not pdf_bytes or not questions:
    st.warning("Waiting for teacher to upload exam.")
    st.stop()

# Show PDF and answer sheet
col1, col2 = st.columns([1.3, 1])
with col1:
    st.subheader("📄 Exam Paper")
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for i in range(len(doc)):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        img = Image.open(BytesIO(pix.tobytes("png")))
        st.image(img, caption=f"Page {i+1}", use_container_width=True)
        st.markdown("---")

with col2:
    st.subheader("✍️ Answer Sheet")
    # Timer and form (same as before, but using questions list)
    # ... (copy the rest of the answer form code from previous version)
    # For brevity, I'll include the essential parts:
    timer_placeholder = st.empty()
    if st.session_state.timer_running:
        elapsed = datetime.now() - st.session_state.start_time
        remaining = timedelta(minutes=timer_minutes) - elapsed
        if remaining.total_seconds() <= 0:
            st.warning("Time's up!")
            st.session_state.submitted = True
            st.session_state.timer_running = False
            st.rerun()
        else:
            timer_placeholder.info(f"⏳ {str(remaining).split('.')[0]}")
            time.sleep(1)
            st.rerun()

    if not st.session_state.submitted:
        with st.form("exam_form"):
            st.write(f"Answer {len(questions)} questions.")
            for idx, q in enumerate(questions):
                q_key = f"Q{idx+1}"
                st.markdown(f"**{idx+1}. {q.get('question', 'MISSING')}**")
                if "options" in q:
                    opts = q["options"]
                    default = 0
                    if q_key in st.session_state.answers and st.session_state.answers[q_key] in opts:
                        default = opts.index(st.session_state.answers[q_key])
                    ans = st.radio("", opts, key=f"ans_{idx}", index=default, label_visibility="collapsed")
                else:
                    default = st.session_state.answers.get(q_key, "")
                    ans = st.text_input("", value=default, key=f"ans_{idx}", label_visibility="collapsed")
                st.session_state.answers[q_key] = ans

            if st.form_submit_button("✅ Submit"):
                st.session_state.start_time = datetime.now()
                st.session_state.timer_running = True
                st.session_state.submitted = True
                # grading...
                score = 0
                fb = {}
                for i, q in enumerate(questions):
                    u = st.session_state.answers.get(f"Q{i+1}", "")
                    c = q.get("correct")
                    if c and str(u).strip().upper() == str(c).strip().upper():
                        score += 1
                        fb[f"Q{i+1}"] = "✅"
                    else:
                        fb[f"Q{i+1}"] = f"❌ (correct: {c})"
                st.session_state.score = score
                st.session_state.feedback = fb
                st.rerun()
    else:
        st.success("Exam submitted!")
        st.metric("Score", f"{st.session_state.score}/{len(questions)}")
        with st.expander("Feedback"):
            for k, v in st.session_state.feedback.items():
                st.write(f"{k}: {v}")
        if st.button("New Exam"):
            for k in default_session:
                if k in st.session_state: del st.session_state[k]
            st.rerun()
