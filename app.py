import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
import time
import fitz  # PyMuPDF
from io import BytesIO
from PIL import Image

# ---------------------------- PAGE CONFIG ----------------------------
st.set_page_config(page_title="Computer-Based Exam", layout="wide")

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

# ---------------------------- GLOBAL CACHE PARA SA EXAM FILES ---------
@st.cache_resource(ttl=3600)  # mag-e-expire after 1 hour para pwede magbago
def get_exam_files():
    """Return dictionary with pdf_bytes and questions_data (or None if not set)."""
    return {"pdf_bytes": None, "questions": None, "pdf_name": None}

# ---------------------------- SIDEBAR (Teacher/Admin Panel) ----------
st.sidebar.header("🛠️ Admin Panel (Teacher Only)")

# Password protection para sa upload (para hindi basta-basta makapagpalit ang estudyante)
admin_password = st.sidebar.text_input("🔑 Admin Password", type="password")
CORRECT_PASSWORD = "exam2026"  # Palitan ito ng gusto mong password

if admin_password == CORRECT_PASSWORD:
    st.sidebar.success("✅ Admin mode activated")
    
    # 1. PDF Upload
    uploaded_pdf = st.sidebar.file_uploader("📄 Upload Exam PDF", type=["pdf"])
    # 2. JSON Upload
    uploaded_json = st.sidebar.file_uploader("📊 Upload Questions JSON", type=["json"])
    
    if st.sidebar.button("📤 Set as Current Exam"):
        exam_files = get_exam_files()
        if uploaded_pdf:
            exam_files["pdf_bytes"] = uploaded_pdf.getvalue()
            exam_files["pdf_name"] = uploaded_pdf.name
        if uploaded_json:
            try:
                exam_files["questions"] = json.load(uploaded_json)
                st.sidebar.success(f"✅ Exam set! {len(exam_files['questions'])} questions loaded.")
            except Exception as e:
                st.sidebar.error(f"❌ Invalid JSON: {e}")
        # Force cache update
        st.cache_resource.clear()
        st.rerun()
else:
    st.sidebar.info("👩‍🏫 Enter admin password to upload exam.")

# I-load ang exam files mula sa cache (available sa lahat ng session)
exam_files = get_exam_files()
pdf_bytes = exam_files.get("pdf_bytes")
questions = exam_files.get("questions")
pdf_name = exam_files.get("pdf_name")

# ---------------------------- TIMER SETTING --------------------------
st.sidebar.header("⏱️ Exam Settings")
timer_minutes = st.sidebar.number_input("Exam Duration (minutes)", min_value=1, max_value=180, value=60, step=5)

# Zoom control para sa PDF (lalabas lang kung may PDF)
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

# Kung walang exam files sa cache, magpakita ng instruction
if not pdf_bytes or not questions:
    st.warning("⏳ Waiting for teacher to upload the exam. Please wait...")
    st.stop()  # Itigil ang app dito hangga't walang exam

# May exam na, ipakita sa dalawang column
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
            
            # Download button per page (high-res)
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
    
    # ---------------------------- TIMER ------------------------------
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
    
    # ---------------------------- ANSWER FORM ------------------------
    if not st.session_state.submitted:
        with st.form("exam_form"):
            st.write(f"Sagutin ang {len(questions)} na tanong.")
            for idx, q in enumerate(questions, start=1):
                q_key = f"Q{idx}"
                st.markdown(f"**{idx}. {q['question']}**")
                
                if "options" in q:  # Multiple choice
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
                elif q.get("type") == "number":  # Number input
                    default = st.session_state.answers.get(q_key, 0.0)
                    answer = st.number_input(
                        "Ilagay ang numero:",
                        value=default,
                        key=f"ans_{idx}",
                        label_visibility="collapsed"
                    )
                else:  # Text input
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
                        feedback[q_key] = "ℹ️ Walang tamang sagot na nakaset"
                
                st.session_state.score = score
                st.session_state.feedback = feedback
                st.rerun()
    else:
        # ---------------------------- RESULTS ----------------------------
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
        
        # Download answers as CSV
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
