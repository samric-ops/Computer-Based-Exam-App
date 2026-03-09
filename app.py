import streamlit as st
import base64
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
    "questions": None,
    "current_page": 0
}
for key, value in default_session.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------------------- SIDEBAR (Teacher Panel) ----------------
st.sidebar.header("🛠️ Teacher Panel")

# 1. PDF Upload (optional)
pdf_file = st.sidebar.file_uploader("📄 Upload Exam PDF (optional)", type=["pdf"])

# 2. JSON Upload (required for auto-grading)
json_file = st.sidebar.file_uploader("📊 Upload Questions JSON", type=["json"], help="Kailangan ito para magkaroon ng automatic scoring.")

# 3. Timer Setting
timer_minutes = st.sidebar.number_input("⏱️ Exam Duration (minutes)", min_value=1, max_value=180, value=60, step=5)

# 4. Zoom control (lalabas lang kung may PDF)
if pdf_file:
    zoom_level = st.sidebar.slider("🔍 Zoom Level", min_value=1.0, max_value=4.0, value=2.5, step=0.1, help="Mas mataas = mas malaki ang text")

# Load questions from JSON
if json_file and st.session_state.questions is None:
    try:
        st.session_state.questions = json.load(json_file)
        st.sidebar.success(f"✅ Na-load ang {len(st.session_state.questions)} na tanong.")
    except Exception as e:
        st.sidebar.error(f"❌ Error sa pagbasa ng JSON: {e}")

# ---------------------------- MAIN UI ---------------------------------
st.title("📝 Computer-Based Exam with Automatic Scoring")

# Display PDF as images if uploaded
if pdf_file:
    col1, col2 = st.columns([1.3, 1])  # Mas malawak na space para sa PDF
    with col1:
        st.subheader("📄 Exam Paper")
        
        try:
            pdf_bytes = pdf_file.getvalue()
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            total_pages = len(pdf_document)
            
            # Page navigation
            if total_pages > 1:
                nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])
                with nav_col1:
                    if st.button("◀ Previous") and st.session_state.current_page > 0:
                        st.session_state.current_page -= 1
                with nav_col2:
                    st.write(f"Page {st.session_state.current_page + 1} of {total_pages}")
                with nav_col3:
                    if st.button("Next ▶") and st.session_state.current_page < total_pages - 1:
                        st.session_state.current_page += 1
            
            # Display current page with high resolution
            page = pdf_document.load_page(st.session_state.current_page)
            matrix = fitz.Matrix(zoom_level, zoom_level)  # Zoom based on slider
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            img_data = pix.tobytes("png")
            img = Image.open(BytesIO(img_data))
            
            # Use container width but ensure high quality
            st.image(img, caption=f"Page {st.session_state.current_page + 1}", use_container_width=True)
            
            # Option to open full screen (new tab)
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            st.download_button(
                "🔍 Buksan sa bagong tab (malaki)",
                data=img_bytes.getvalue(),
                file_name=f"page_{st.session_state.current_page+1}.png",
                mime="image/png"
            )
            
            pdf_document.close()
        except Exception as e:
            st.error(f"❌ Hindi mabuksan ang PDF: {e}")
            st.info("Subukan mong i-download ang PDF sa ibaba.")
            st.download_button("📥 I-download ang PDF", data=pdf_bytes, file_name="exam.pdf")
        
    answer_col = col2
else:
    st.subheader("✍️ Answer Sheet")
    answer_col = st.container()

# ---------------------------- TIMER -----------------------------------
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

# ---------------------------- ANSWER FORM ----------------------------
with answer_col:
    if not st.session_state.submitted:
        if st.session_state.questions is None:
            st.warning("⚠️ Maghintay ng instruction mula sa teacher. (Kailangan mag-upload ng JSON file sa sidebar.)")
        else:
            with st.form("exam_form"):
                st.write(f"Sagutin ang {len(st.session_state.questions)} na tanong.")
                for idx, q in enumerate(st.session_state.questions, start=1):
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
                    for idx, q in enumerate(st.session_state.questions, start=1):
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
            total = len(st.session_state.questions)
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
