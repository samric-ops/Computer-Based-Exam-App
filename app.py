import streamlit as st
import base64

st.set_page_config(page_title="Math Exam Portal", layout="wide")

st.title("📝 Professional Exam Portal")
st.sidebar.header("Teacher Dashboard")

# Dito mo i-uupload ang PDF version ng exam mo
uploaded_file = st.sidebar.file_uploader("Upload your Exam (PDF only)", type=["pdf"])

if uploaded_file is not None:
    # Ipakita ang PDF sa screen
    base64_pdf = base64.b64encode(uploaded_file.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="1000" type="application/pdf"></iframe>'
    
    st.markdown(pdf_display, unsafe_allow_html=True)
    
    # Lagayan ng sagot sa ilalim
    with st.form("answers"):
        st.write("### I-type ang inyong mga sagot dito:")
        ans1 = st.text_input("Question 1")
        ans2 = st.text_input("Question 2")
        # Dagdagan mo lang ito base sa dami ng questions
        
        submitted = st.form_submit_button("Submit Exam")
        if submitted:
            st.success("Tapos na! Na-record na ang iyong mga sagot.")
else:
    st.info("Teacher: Pakibukas ang sidebar sa kaliwa at i-upload ang PDF version ng exam.")
