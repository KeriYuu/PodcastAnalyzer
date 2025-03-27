import os
# Set environment variables to resolve OpenMP duplicate loading issue
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'

import streamlit as st
import time
from pydub import AudioSegment
from transcribe import transcribe_audio
import os

def render_transcribe_section(st):
    """
    Render transcription section (aligned with API server version)
    """
    if not st.session_state.get("download_completed"):
        st.warning("Please download the audio file first", icon="⚠️")
        return

    transcript_dir = "transcript_files"
    os.makedirs(transcript_dir, exist_ok=True)
    
    # Point 1: Support multiple output formats
    output_format = st.selectbox(
        "Output Format",
        ["txt", "srt", "json"],
        index=0,
        help="Select the output format for transcription"
    )
    
    transcript_filename = f"{st.session_state.podcast_title}.{output_format}"
    transcript_path = os.path.join(transcript_dir, transcript_filename)

    # Point 2: Unified mode naming convention
    transcribe_mode = st.radio(
        "Select Transcription Mode",
        ["local", "api"],
        format_func=lambda x: "Local Transcription" if x == "local" else "API Transcription",
        help="Local mode uses local model, API mode uses self-hosted Whisper service"
    )

    # Point 3: Update API endpoint configuration
    api_url = None
    if transcribe_mode == "api":
        api_url = st.text_input(
            "API Endpoint URL",
            value="http://localhost:8000/transcribe",  # Align with server default port
            help="Enter the complete API endpoint URL (e.g., http://ip:port/transcribe)"
        )
        if not api_url:
            st.warning("API mode requires a valid server URL", icon="⚠️")
            return

    if st.button("Start Transcription", type="primary"):
        progress_bar = st.progress(0)
        status_message = st.empty()
        
        def update_progress(progress, message):
            progress_bar.progress(progress)
            status_message.text(message)

        try:
            # Point 4: Align parameters with API server
            transcript = transcribe_audio(
                audio_path=st.session_state.audio_path,
                output_file=transcript_filename,
                output_format=output_format,  # Dynamic format support
                device_option="cpu",
                mode=transcribe_mode,  # Use unified mode identifier
                api_url=api_url,
                progress_callback=update_progress
            )
            
            st.session_state.transcript = transcript
            st.session_state.transcript_path = transcript_path
            st.session_state.transcribe_completed = True
            
            st.success("Transcription completed!", icon="✅")
            st.code(f"File location: {os.path.abspath(transcript_path)}")

        except Exception as e:
            # Point 5: Enhanced error handling
            error_msg = str(e)
            if "400" in error_msg:
                st.error(f"Request error: {error_msg.split('detail')[-1]}", icon="🚨")
            elif "422" in error_msg:
                st.error(f"Processing error: {error_msg.split('detail')[-1]}", icon="🚧")
            else:
                st.error(f"Transcription failed: {error_msg}", icon="❌")
            st.session_state.transcribe_completed = False

    if st.session_state.get("transcribe_completed"):
        st.markdown("### 📝 Transcription Info")
        st.markdown(f"""
        - **Filename**: `{transcript_filename}`
        - **Path**: `{transcript_path}`
        - **Size**: `{os.path.getsize(transcript_path)/1024:.1f} KB`
        """)