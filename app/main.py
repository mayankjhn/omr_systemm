import streamlit as st
import pandas as pd
import json
from omr_processor import OMRProcessor

st.set_page_config(layout="wide")
st.title("🎯 OMR Evaluation for Hackathon")

@st.cache_resource
def get_processor():
    return OMRProcessor(debug=st.session_state.get('debug_mode', True))

def main():
    if 'debug_mode' not in st.session_state: st.session_state.debug_mode = True
    processor = get_processor()
    processor.debug = st.session_state.debug_mode

    with st.sidebar:
        st.header("⚙️ Controls")
        st.session_state.debug_mode = st.checkbox("Enable Debug Mode", value=st.session_state.debug_mode)
        st.header("🔑 Answer Key")
        uploaded_key = st.file_uploader("Upload Answer Key (JSON)", type="json")
        st.header("📄 OMR Sheets")
        uploaded_files = st.file_uploader("Upload Hackathon OMR Images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    if uploaded_key:
        try:
            st.session_state.answer_key = {str(k): v for k, v in json.load(uploaded_key).items()}
            st.sidebar.success(f"{len(st.session_state.answer_key)} questions loaded.")
        except Exception: st.sidebar.error("Invalid JSON key file.")
    
    if st.sidebar.button("🚀 Process OMR Sheets", disabled=not (uploaded_files and 'answer_key' in st.session_state)):
        st.session_state.results = []
        for uploaded_file in uploaded_files:
            with st.spinner(f"Processing {uploaded_file.name}..."):
                image_bytes = uploaded_file.getvalue()
                result = processor.process_omr_sheet(image_bytes, st.session_state.answer_key)
                
                if result and result.get('error') is None:
                    result['filename'] = uploaded_file.name
                    st.session_state.results.append(result)
                    st.success(f"{uploaded_file.name}: Score = {result.get('percentage', 0):.2f}%")
                    if processor.debug and processor.processed_image_for_debug is not None:
                        st.image(processor.processed_image_for_debug, caption=f"Debug: {uploaded_file.name}")
                else:
                    st.error(f"Failed to process {uploaded_file.name}: {result.get('error', 'Unknown')}")

    if 'results' in st.session_state and st.session_state.results:
        st.header("📊 Results")
        df = pd.DataFrame(st.session_state.results)
        st.dataframe(df[['filename', 'correct', 'total_questions', 'percentage']])

if __name__ == "__main__":
    main()
