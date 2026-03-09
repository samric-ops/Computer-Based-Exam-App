import streamlit as st
import json

# Set up the professional page look
st.set_page_config(page_title="Professional Math Exam", page_icon="📝", layout="centered")

# Custom Styling
st.markdown("""
    <style>
    .stRadio > label { font-size: 18px; font-weight: bold; }
    .main { background-color: #fafafa; }
    </style>
    """, unsafe_allow_html=True)

def load_exam_data():
    try:
        with open('questions.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ 'questions.json' not found. Please upload it to your GitHub repo.")
        return None
    except json.JSONDecodeError as e:
        st.error(f"❌ Syntax Error in questions.json: {e}")
        st.info("Ensure you used double backslashes (\\\\) for math and closed all commas.")
        return None

def main():
    st.title("📐 Modern Mathematics Exam")
    st.write("Complete the exam below. Math formulas are displayed in professional LaTeX format.")
    st.divider()

    questions = load_exam_data()
    
    if questions:
        responses = {}
        
        with st.form("exam_submission"):
            for q in questions:
                st.subheader(f"Question {q['id']}")
                st.write(q['question'])
                
                # Render Professional Math
                if q['math_content']:
                    st.latex(q['math_content'])
                
                # Input type
                if q['type'] == "multiple_choice":
                    responses[q['id']] = st.radio("Choose the correct answer:", q['options'], key=f"q_{q['id']}")
                else:
                    responses[q['id']] = st.text_input("Type your answer:", key=f"q_{q['id']}")
                
                st.divider()

            # Submit button
            submitted = st.form_submit_button("Submit My Answers")

        if submitted:
            score = 0
            for q in questions:
                if responses[q['id']] == q['answer']:
                    score += 1
            
            st.balloons()
            st.success(f"### Submission Successful!")
            st.metric(label="Final Score", value=f"{score} / {len(questions)}")
            
            if score == len(questions):
                st.confetti() # Only if using extra components, otherwise just balloons is fine
                st.write("Excellent! Perfect score! 🌟")

if __name__ == "__main__":
    main()
