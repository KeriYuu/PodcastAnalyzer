import os
# Set environment variables to resolve OpenMP duplicate loading issue
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'

import streamlit as st
import torch
from pydub import AudioSegment
torch.classes.__path__ = []

# Set page configuration to use wide mode
st.set_page_config(
    layout="wide",
    page_title="Xiaoyuzhou -> Notion"
)

from download_ui import render_download_section
from transcribe_ui import render_transcribe_section
from analyze import render_analysis_section
from file_manager_ui import render_file_manager_section
from state_manager import init_session_state
from utils import format_duration

# Set page title
st.title("Xiaoyuzhou -> Notion")

# Initialize session state
init_session_state()

# Create four-column layout
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

# Top left: Download section
with col1:
    download_expander = st.expander(
        "Step 1: Download Podcast",
        expanded=not st.session_state.download_completed
    )
    with download_expander:
        render_download_section(st)
        # Audio display section
        if st.session_state.download_completed:
            st.subheader("Downloaded Audio")
            st.write(f"**Title**: {st.session_state.podcast_title}")
            
            # Get audio information
            audio = AudioSegment.from_file(st.session_state.audio_path)
            duration = audio.duration_seconds
            readable_duration = format_duration(duration)
            file_size = os.path.getsize(st.session_state.audio_path) / 1024 / 1024
            
            # Display audio information in horizontal layout
            st.write(f"**Duration**: {readable_duration} | **File Size**: {file_size:.2f} MB")
            
            # Display shownotes if available
            if hasattr(st.session_state, 'shownotes') and st.session_state.shownotes:
                st.subheader("Podcast Shownotes")
                st.text_area("Show Notes Content", 
                           st.session_state.shownotes, 
                           height=200,
                           help="Podcast description and key points")

# Top right: File management section
with col2:
    file_manager_expander = st.expander(
        "Step 2: File Management",
        expanded=True
    )
    with file_manager_expander:
        render_file_manager_section(st)

# Bottom left: Transcription section
with col3:
    transcribe_expander = st.expander(
        "Step 3: Transcribe Audio",
        expanded=st.session_state.download_completed
    )
    with transcribe_expander:
        render_transcribe_section(st)
        # Transcription result display
        if st.session_state.transcript:
            st.subheader("Transcription Preview")
            st.text_area("Transcript Content", 
                        st.session_state.transcript, 
                        height=400,
                        help="You can edit the transcription content here")

# Bottom right: Analysis section
with col4:
    analysis_expander = st.expander(
        "Step 4: AI Podcast Analysis",
        expanded=bool(st.session_state.transcript)
    )
    with analysis_expander:
        render_analysis_section(st)

# ================= Style Adjustments =================
st.markdown("""
<style>
    h3 {
        font-size: 1rem !important;     
    }
    .stButton>button {
        transition: all 0.3s ease;
        background-color: white;
        color: #1f77b4;
        border: 1px solid #1f77b4;
        border-radius: 4px;
    }
    .stButton>button:focus,
    .stButton>button:active {
        background-color: #f0f0f0 !important;  
        color: #666666 !important;            
        border-color: #cccccc !important; 
        box-shadow: none;
    }
    
    /* Border style */
    [data-testid="stExpander"] details {
        background: #f0f8ff;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(31, 119, 180, 0.1);
        border: 1px solid #1f77b4;
    }
    
    /* Increase maximum width of content area */
    .main .block-container {
        max-width: 800px;
        padding-top: 2rem;
    }
    
    /* Adjust title font size and color */
    [data-testid="stExpander"] summary {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1f77b4;
    }
    
    /* Adjust subtitle font size and color */
    .element-container h3 {
        font-size: 1.2rem;
        color: #2c8ac4;
    }
    
    /* Adjust body text font size and color */
    .element-container p, .element-container div {
        font-size: 1rem;
        color: #333;
    }
    
    /* Adjust input box style */
    .stTextInput input, .stTextArea textarea {
        border-color: #1f77b4;
    }
    
    /* Adjust select box style */
    .stSelectbox select {
        border-color: #1f77b4;
    }
    
    /* Adjust progress bar style */
    .stProgress .st-bo {
        background-color: #1f77b4;
    }
    
    /* Adjust warning and success message style */
    .stAlert {
        border-color: #1f77b4;
    }
    
    /* Adjust code block style */
    .stCodeBlock {
        background-color: #f0f8ff;
        border: 1px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)