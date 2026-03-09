import streamlit as st
import json

# 1. Page Configuration
st.set_page_config(page_title="Digital Exam System", layout="wide")

# 2. Sidebar - Teacher/Admin Controls
st.sidebar.title("🛠️ Teacher Dashboard")
st.sidebar.info("Upload your 'questions.json' file here to generate the exam for your students.")

uploaded_file = st.sidebar.file_uploader("Upload Exam File (JSON)", type=["json"])

# 3. Session State to store the exam
if uploaded_file is not None:
    try:
        st.session_state.exam_data = json.load(uploaded_file)
        st.sidebar.success("✅ Exam Uploaded Successfully!")
    except Exception as e:
        st.sidebar.error(f"❌ Error: {e}")

# 4. Main App Logic
st.title("📝 Student Exam Portal")

if 'exam_data' not in st.session_state:
    st.warning("👋 Welcome! Please wait for your teacher to upload the exam file in the dashboard.")
else:
    st.info("💡 Instructions: Read the questions carefully. Math symbols are displayed professionally.")
    
    questions = st.session_state.exam_data
    responses = {}

    # The Exam Form
    with st.form("student_exam"):
        for i, q in enumerate(questions):
            st.markdown(f"### Question {i+1}")
            st.write(q['question_text'])
            
            # This renders the "Professional" Math (Fractions/Exponents)
            if "math_formula" in q and q['math_formula']:
                st.latex(q['math_formula'])
            
            # Answer input
            if q['type'] == "multiple_choice":
                responses[i] = st.radio("Choose the best answer:", q['options'], key=f"q_{i}")
            else:
                responses[i] = st.text_input("Type your answer here:", key=f"q_{i}")
            
            st.divider()

        # Submit
        submitted = st.form_submit_button("Submit Final Answers")

    if submitted:
        score = 0
        total = len(questions)
        
        for i, q in enumerate(questions):
            if responses[i] == q['correct_answer']:
                score += 1
        
        st.balloons()
        st.success(f"### Exam Submitted!")
        st.metric(label="Your Final Score", value=f"{score} / {total}")
        st.write("Results have been recorded. You may now close this tab.")
