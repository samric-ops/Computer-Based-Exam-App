if pdf_file:
    st.subheader("📄 Exam Paper")
    bytes_data = pdf_file.getvalue()
    
    st.info("""
    ⚠️ **Hindi ma-display ang PDF sa browser na ito.**
    
    **Para mabasa ang exam:**
    1. I-click ang button sa ibaba para i-download ang PDF
    2. Buksan ang na-download na file
    3. Balikan ang tab na ito para sagutan ang exam
    """)
    
    st.download_button(
        "📥 I-download ang Exam PDF",
        data=bytes_data,
        file_name="exam.pdf",
        mime="application/pdf"
    )
