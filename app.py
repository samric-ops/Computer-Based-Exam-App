import streamlit as st
import json
import pandas as pd
import os
import time
from datetime import datetime, timedelta
import fitz  # PyMuPDF
from io import BytesIO
from PIL import Image

# ---------------------------- PAGE CONFIG ----------------------------
st.set_page_config(page_title="Computer-Based Exam", layout="wide")

# ---------------------------- PATHS FOR SHARED FILES -----------------
PDF_PATH = "/tmp/exam.pdf"
JSON_PATH = "/tmp/exam_questions.json"

# ---------------------------- SESSION STATE INIT --------------------
default_session = {
    "answers": {},
    "submitted": False,
    "start_time": None,
    "timer_running": False,
    "score": None,
    "feedback": {},
    "questions": None
}
for key, value in default_session.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------------------- SIDEBAR (Teacher/Admin Panel) ----------
st.sidebar.header("🛠️ Admin Panel (Teacher Only)")

admin_password = st.sidebar.text_input("🔑 Admin Password", type="password")
CORRECT_PASSWORD = "exam2024"

if admin_password == CORRECT_PASSWORD:
    st.sidebar.success("✅ Admin mode activated")
    
    uploaded_pdf = st.sidebar.file_uploader("📄 Upload Exam PDF", type=["pdf"])
    uploaded_json = st.sidebar.file_uploader("📊 Upload Questions JSON", type=["json"])
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("📤 Set as Current Exam"):
            if uploaded_pdf:
                with open(PDF_PATH, "wb") as f:
                    f.write(uploaded_pdf.getvalue())
                st.sidebar.success("✅ PDF saved")
            
            if uploaded_json:
                try:
                    raw_data = json.load(uploaded_json)
                    # I-save ang original para makita sa debug
                    with open(JSON_PATH, "w") as f:
                        json.dump(raw_data, f)
                    st.sidebar.success(f"✅ JSON saved")
                except Exception as e:
                    st.sidebar.error(f"❌ Error reading JSON: {e}")
            
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Exam"):
            for path in [PDF_PATH, JSON_PATH]:
                if os.path.exists(path):
                    os.remove(path)
            st.sidebar.success("✅ Exam cleared")
            st.rerun()
    
    # DEBUG: Show raw JSON content
    with st.sidebar.expander("🔍 JSON Debug Viewer", expanded=True):
        if os.path.exists(JSON_PATH):
            try:
                with open(JSON_PATH, "r") as f:
                    debug_json = json.load(f)
                st.write("**Raw JSON content:**")
                st.json(debug_json)  # Streamlit JSON viewer
                st.write(f"**Type:** {type(debug_json)}")
                if isinstance(debug_json, list):
                    st.write(f"**Length:** {len(debug_json)}")
                    if len(debug_json) > 0:
                        st.write("**First item:**")
                        st.write(debug_json[0])
                elif isinstance(debug_json, dict):
                    st.write(f"**Keys:** {list(debug_json.keys())}")
            except Exception as e:
                st.write(f"Error reading JSON: {e}")
        else:
            st.write("No JSON file found.")
else:
    st.sidebar.info("👩‍🏫 Enter admin password to upload exam.")

# ---------------------------- LOAD SHARED EXAM FILES -----------------
pdf_bytes = None
questions = None
pdf_name = None
json_error = None

if os.path.exists(PDF_PATH):
    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()
    pdf_name = os.path.basename(PDF_PATH)

if os.path.exists(JSON_PATH):
    try:
        with open(JSON_PATH, "r") as f:
            raw = json.load(f)
        
        # Intelligent extraction
        if isinstance(raw, list):
            questions = raw
        elif isinstance(raw, dict):
            # Try common keys
            if "questions" in raw:
                questions = raw["questions"]
            elif "exam" in raw:
                questions = raw["exam"]
            elif "quiz" in raw:
                questions = raw["quiz"]
            elif "data" in raw:
                questions = raw["data"]
            else:
                # Maybe it's a single question object?
                if "question" in raw:
                    questions = [raw]  # Wrap as list
                else:
                    questions = None
                    json_error = "No recognizable question array found."
        else:
            questions = None
            json_error = "JSON is neither list nor dict."
    except Exception as e:
        json_error = str(e)
        questions = None

# ---------------------------- TIMER SETTING --------------------------
st.sidebar.header("⏱️ Exam Settings")
timer_minutes = st.sidebar.number_input("Exam Duration (minutes)", min_value=1, max_value=180, value=60, step=5)

if pdf_bytes:
    zoom_level = st.sidebar.slider(
        "🔍 Zoom Level",
        min_value=2.0,
        max_value=5.0,
        value=3.0,
        step=0.2
    )

# ---------------------------- MAIN UI ---------------------------------
st.title("📝 Computer-Based Exam with Automatic Scoring")

# Display debug info in main area if something's wrong
if json_error:
    st.error(f"JSON Error: {json_error}")

if not pdf_bytes:
    st.warning("⏳ Waiting for teacher to upload the exam (PDF missing).")
    st.stop()

if not questions:
    st.warning("⏳ Waiting for teacher to upload the exam (JSON missing or invalid).")
    st.stop()

if len(questions) == 0:
    st.error("⚠️ The JSON file contains no questions.")
    st.stop()

# Display exam in two columns
col1, col2 = st.columns([1.3, 1])

with col1:
    st.subheader(f"📄 Exam Paper: {pdf_name}")
    
    try:
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(pdf_document)
        st.info(f"📄 May {total_pages} na pahina. Mag-scroll pababa.")
        
        for page_num in range(total_pages):
            page = pdf_document.load_page(page_num)
            matrix = fitz.Matrix(zoom_level, zoom_level)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            img_data = pix.tobytes("png")
            img = Image.open(BytesIO(img_data))
            st.image(img, caption=f"Pahina {page_num + 1}", use_container_width=True)
            st.markdown("---")
        
        pdf_document.close()
    except Exception as e:
        st.error(f"❌ Error displaying PDF: {e}")

with col2:
    st.subheader("✍️ Answer Sheet")
    
    # Timer
    timer_placeholder = st.empty()
    if st.session_state.timer_running:
        elapsed = datetime.now() - st.session_state.start_time
        remaining = timedelta(minutes=timer_minutes) - elapsed
        if remaining.total_seconds() <= 0:
            st.warning("⏰ Tapos na ang oras!")
            st.session_state.submitted = True
            st.session_state.timer_running = False
            st.rerun()
        else:
            timer_placeholder.info(f"⏳ Oras: {str(remaining).split('.')[0]}")
            time.sleep(1)
            st.rerun()
    
    # Answer form
    if not st.session_state.submitted:
        with st.form("exam_form"):
            st.write(f"Sagutin ang {len(questions)} na tanong.")
            
            for idx, q in enumerate(questions, start=1):
                q_key = f"Q{idx}"
                
                # Safe question display
                if not isinstance(q, dict):
                    st.error(f"Question {idx} is not a valid object.")
                    continue
                
                question_text = q.get("question", f"[NO QUESTION TEXT {idx}]")
                st.markdown(f"**{idx}. {question_text}**")
                
                # Input type detection
                if "options" in q and isinstance(q["options"], list):
                    options = q["options"]
                    default_index = 0
                    if q_key in st.session_state.answers and st.session_state.answers[q_key] in options:
                        default_index = options.index(st.session_state.answers[q_key])
                    answer = st.radio(
                        "Piliin:",
                        options,
                        key=f"ans_{idx}",
                        index=default_index,
                        label_visibility="collapsed"
                    )
                elif q.get("type") == "number":
                    default = st.session_state.answers.get(q_key, 0.0)
                    answer = st.number_input(
                        "Numero:",
                        value=default,
                        key=f"ans_{idx}",
                        label_visibility="collapsed"
                    )
                else:
                    default = st.session_state.answers.get(q_key, "")
                    answer = st.text_input(
                        "Sagot:",
                        value=default,
                        key=f"ans_{idx}",
                        label_visibility="collapsed"
                    )
                
                st.session_state.answers[q_key] = answer
            
            submitted = st.form_submit_button("✅ Isumite ang mga Sagot")
            
            if submitted:
                if not st.session_state.timer_running and timer_minutes > 0:
                    st.session_state.start_time = datetime.now()
                    st.session_state.timer_running = True
                
                st.session_state.submitted = True
                
                # Auto-grading
                score = 0
                feedback = {}
                for idx, q in enumerate(questions, start=1):
                    q_key = f"Q{idx}"
                    user_ans = st.session_state.answers.get(q_key, "")
                    correct = q.get("correct")
                    if correct is not None:
                        if str(user_ans).strip().upper() == str(correct).strip().upper():
                            score += 1
                            feedback[q_key] = "✅ Tama"
                        else:
                            feedback[q_key] = f"❌ Mali (Tamang sagot: {correct})"
                    else:
                        feedback[q_key] = "ℹ️ Walang tamang sagot"
                
                st.session_state.score = score
                st.session_state.feedback = feedback
                st.rerun()
    else:
        st.success("✅ Naipasa na ang eksamen!")
        
        if st.session_state.score is not None:
            total = len(questions)
            st.metric("Marka", f"{st.session_state.score} / {total}")
            
            with st.expander("📋 Feedback"):
                for q_key, fb in st.session_state.feedback.items():
                    st.write(f"{q_key}: {fb}")
        
        st.write("### 📝 Iyong mga Sagot")
        for q_key, ans in st.session_state.answers.items():
            st.write(f"{q_key}: {ans}")
        
        # Download CSV
        df = pd.DataFrame(list(st.session_state.answers.items()), columns=["Tanong", "Sagot"])
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 I-download CSV", data=csv, file_name="my_answers.csv", mime="text/csv")
        
        if st.button("🔄 Muling Mag-exam"):
            for key in default_session.keys():
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
