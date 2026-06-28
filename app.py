# app.py
import streamlit as st
import os
from dotenv import load_dotenv
from graph import study_agent_graph

st.set_page_config(page_title="PDF Study Notes Generator", page_icon="📄", layout="centered")
load_dotenv()

st.title("📄 YouTube PDF Notes Generator")
st.write("Convert any technical or educational video into a beautifully formatted PDF study guide.")

video_url_input = st.text_input("Paste YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Generate  PDF", type="primary"):
    if not video_url_input.strip():
        st.warning("Please provide a valid link first.")
    else:
        with st.spinner("Analyzing transcript and designing layout structure..."):
            try:
                final_state = study_agent_graph.invoke({'video_url': video_url_input})
                
                if final_state.get('error_message'):
                    st.error(f"❌ Error: {final_state['error_message']}")
                else:
                    st.success("✅ PDF Document Drafted Successfully!")
                    
                    # Preview the text notes on screen
                    with st.expander("📝 View Notes Preview"):
                        st.markdown(final_state['summary'])
                    
                    # Read generated PDF bytes to feed Streamlit download engine
                    pdf_path = final_state['pdf_path']
                    if os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as pdf_file:
                            pdf_bytes = pdf_file.read()
                        
                        st.divider()
                        st.download_button(
                            label="📥 Download Structured PDF",
                            data=pdf_bytes,
                            file_name="Structured_Study_Notes.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        
                        # Cleanup temp file from workspace after loading into memory
                        os.remove(pdf_path)
            except Exception as e:
                st.error(f"System Error: {str(e)}")
