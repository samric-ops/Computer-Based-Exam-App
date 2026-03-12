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

# Password protection
admin_password = st.sidebar.text_input("🔑 Admin Password", type="password")
CORRECT_PASSWORD = "exam2024"  # Palitan kung gusto

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
                    # Auto-detect: kung may "questions" key, i-extract
                    if isinstance(raw_data, dict) and "questions" in raw_data:
                        questions_data = raw_data["questions"]
                    elif isinstance(raw_data, list):
                        questions_data = raw_data
                    else:
                        st.sidebar.error("❌ Invalid JSON format: dapat list o { 'questions': [...] }")
                        questions_data = None
                    
                    if questions_data is not None:
                        # I-save bilang list (para sure)
                        with open(JSON_PATH, "w") as f:
                            json.dump(questions_data, f)
                        st.sidebar.success(f"✅ JSON saved with {len(questions_data)} questions")
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
    
    # Debug info
    with st.sidebar.expander("📁 File Status", expanded=True):
        st.write(f"PDF exists: {os.path.exists(PDF_PATH)}")
        if os.path.exists(PDF_PATH):
            st.write(f"PDF size: {os.path.getsize(PDF_PATH)} bytes")
        st.write(f"JSON exists: {os.path.exists(JSON_PATH)}")
        if os.path.exists(JSON_PATH):
            st.write(f"JSON size: {os.path.getsize(JSON_PATH)} bytes")
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
        # Auto-detect ulit sa loading (kung sakaling may wrapper pa rin)
        if isinstance(raw, dict) and "questions" in raw:
            questions = raw["questions"]
        elif isinstance(raw, list):
            questions = raw
        else:
            questions = None
            json_error = "JSON is neither a list nor an object with 'questions' key"
    except Exception as e:
        json_error = str(e)
        questions = None

# ---------------------------- TIMER SETTING --------------------------
st.sidebar.header("⏱️ Exam Settings")
timer_minutes = st.sidebar.number_input("Exam Duration (minutes)", min_value=1, max_value=180, value=60, step=5)

if pdf_bytes:
    zoom_level = st.sidebar.slider(
        "🔍 Zoom Level (linaw)",
        min_value=2.0,
        max_value=5.0,
        value=3.0,
        step=0.2,
        help="Mas mataas = mas malaki at malinaw ang text."
    )

# ---------------------------- MAIN UI ---------------------------------
st.title("📝 Computer-Based Exam with Automatic Scoring")

# Check if exam files are ready
if not pdf_bytes or not questions:
    st.warning("⏳ Waiting for teacher to upload the exam. Please wait...")
    if json_error:
        st.error(f"JSON error: {json_error}")
    st.stop()

# Display exam in two columns
col1, col2 = st.columns([1.3, 1])

with col1:
    st.subheader(f"📄 Exam Paper: {pdf_name} (lahat ng pages)")
    
    try:
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(pdf_document)
        st.info(f"📄 May {total_pages} na pahina. Mag-scroll pababa para makita lahat.")
        
        for page_num in range(total_pages):
            page = pdf_document.load_page(page_num)
            matrix = fitz.Matrix(zoom_level, zoom_level)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            img_data = pix.tobytes("png")
            img = Image.open(BytesIO(img_data))
            
            st.image(img, caption=f"Pahina {page_num + 1}", use_container_width=True)
            
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            st.download_button(
                f"📥 I-download ang Pahina {page_num + 1} (high-res)",
                data=img_bytes.getvalue(),
                file_name=f"page_{page_num+1}.png",
                mime="image/png",
                key=f"download_page_{page_num}"
            )
            st.markdown("---")
        
        pdf_document.close()
    except Exception as e:
        st.error(f"❌ Error displaying PDF: {e}")

with col2:
    st.subheader("✍️ Answer Sheet")
    
    timer_placeholder = st.empty()
    if st.session_state.timer_running:
        elapsed = datetime.now() - st.session_state.start_time
        remaining = timedelta(minutes=timer_minutes) - elapsed
        if remaining.total_seconds() <= 0:
            st.warning("⏰ Tapos na ang oras! Isinusumite ang iyong mga sagot.")
            st.session_state.submitted = True
            st.session_state.timer_running = False
            st.rerun()
        else:
            timer_placeholder.info(f"⏳ Oras na natitira: {str(remaining).split('.')[0]}")
            time.sleep(1)
            st.rerun()
    
    if not st.session_state.submitted:
        with st.form("exam_form"):
            st.write(f"Sagutin ang {len(questions)} na tanong.")
            for idx, q in enumerate(questions, start=1):
                q_key = f"Q{idx}"
                if not isinstance(q, dict):
                    st.error(f"Invalid question format at index {idx}")
                    continue
                question_text = q.get("question", f"[MISSING QUESTION {idx}]")
                st.markdown(f"**{idx}. {question_text}**")
                
                if "options" in q and isinstance(q["options"], list):
                    options = q["options"]
                    default_index = 0
                    if q_key in st.session_state.answers and st.session_state.answers[q_key] in options:
                        default_index = options.index(st.session_state.answers[q_key])
                    answer = st.radio(
                        "Piliin ang sagot:",
                        options,
                        key=f"ans_{idx}",
                        index=default_index,
                        label_visibility="collapsed"
                    )
                elif q.get("type") == "number":
                    default = st.session_state.answers.get(q_key, 0.0)
                    answer = st.number_input(
                        "Ilagay ang numero:",
                        value=default,
                        key=f"ans_{idx}",
                        label_visibility="collapsed"
                    )
                else:
                    default = st.session_state.answers.get(q_key, "")
                    answer = st.text_input(
                        "Ilagay ang sagot:",
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
                        feedback[q_key] = "ℹ️ Walang tamang sagot na nakaset"
                
                st.session_state.score = score
                st.session_state.feedback = feedback
                st.rerun()
    else:
        st.success("✅ Naipasa na ang iyong eksamen!")
        
        if st.session_state.score is not None:
            total = len(questions)
            st.metric("Iyong Marka", f"{st.session_state.score} / {total}")
            
            with st.expander("📋 Tingnan ang detailed feedback"):
                for q_key, fb in st.session_state.feedback.items():
                    st.write(f"{q_key}: {fb}")
        
        st.write("### 📝 Iyong mga Sagot")
        for q_key, ans in st.session_state.answers.items():
            st.write(f"{q_key}: {ans}")
        
        df = pd.DataFrame(list(st.session_state.answers.items()), columns=["Tanong", "Sagot"])
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 I-download ang mga Sagot (CSV)",
            data=csv,
            file_name="my_answers.csv",
            mime="text/csv"
        )
        
        if st.button("🔄 Muling Mag-exam"):
            for key in default_session.keys():
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
