import streamlit as st
import base64

st.set_page_config(page_title="Professional Math Exam", layout="wide")

# Header
st.title("📝 Computer-Based Math Exam")
st.markdown("---")

# Sidebar para sa Teacher
st.sidebar.header("📂 Teacher Controls")
uploaded_file = st.sidebar.file_uploader("Upload Exam (PDF Format)", type=["pdf"])

if uploaded_file is not None:
    # Column 1: Ang Exam (PDF Display)
    # Column 2: Ang Answer Sheet
    col1, col2 = st.columns([1.5, 1]) # Mas malapad ang column ng exam

    with col1:
        st.subheader("📄 Exam Paper")
        # I-convert ang PDF para ma-embed sa app
        base64_pdf = base64.b64encode(uploaded_file.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

    with col2:
        st.subheader("✍️ Answer Sheet")
        with st.form("exam_form"):
            st.info("I-type ang inyong mga sagot sa ibaba.")
            
            # Halimbawa ng input fields. Pwede mong dagdagan base sa dami ng questions.
            q1 = st.text_input("Question 1:")
            q2 = st.text_input("Question 2:")
            q3 = st.text_input("Question 3:")
            q4 = st.text_input("Question 4:")
            q5 = st.text_input("Question 5:")
            
            submit = st.form_submit_button("Submit Answers")
            
            if submit:
                st.success("✅ Submitted! Your answers have been recorded.")
                # Dito pwede nating ilagay ang logic para i-save ang scores sa Excel/Google Sheets.
else:
    st.warning("👋 Teacher, pakibukas ang Sidebar at i-upload ang PDF version ng iyong Word Exam.")
    st.info("Tip: Sa Word, i-click ang 'Save As' tapos piliin ang 'PDF' para hindi masira ang tables at math symbols.")
