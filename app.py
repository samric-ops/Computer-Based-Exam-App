import streamlit as st
import json

# Page Configuration
st.set_page_config(page_title="Math Exam Portal", layout="centered")

# Custom CSS for professional look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

def load_data():
    with open('questions.json', 'r') as f:
        return json.load(f)

def main():
    st.title("📝 Professional Exam Portal")
    st.info("Instructions: Answer all questions carefully. Math formulas are rendered professionally.")

    questions = load_data()
    responses = {}

    # The Exam Form
    with st.form("exam_form"):
        for q in questions:
            st.write(f"### Question {q['id']}")
            st.write(q['question'])
            
            # This is the "Word-for-Word" professional math renderer
            if q['math_content']:
                st.latex(q['math_content'])
            
            if q['type'] == "multiple_choice":
                responses[q['id']] = st.radio("Select your answer:", q['options'], key=f"q_{q['id']}")
            else:
                responses[q['id']] = st.text_input("Type your answer here:", key=f"q_{q['id']}")
            
            st.divider()

        # Submit Button
        submitted = st.form_submit_button("Submit Exam")

    if submitted:
        st.balloons()
        st.success("Your exam has been submitted!")
        
        # Grading Logic
        score = 0
        for q in questions:
            if responses[q['id']] == q['answer']:
                score += 1
        
        st.metric(label="Your Final Score", value=f"{score} / {len(questions)}")
        st.write("Thank you for completing the exam electronically! 🌱")

if __name__ == "__main__":
    main()
