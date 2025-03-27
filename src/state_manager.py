import streamlit as st

def init_session_state():
    session_defaults = {
        "download_completed": False,
        "audio_path": None,
        "podcast_title": None,
        "podcast_host": None,
        "publish_date": None,
        "podcast_url": None,
        "transcript": None,
        "transcript_path": None,
        "analysis": None,
        "is_analyzing": False,
        "is_transcribing": False
    }

    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def reset_session_state():
    session_defaults = {
        "download_completed": False,
        "audio_path": None,
        "podcast_title": None,
        "podcast_host": None,
        "publish_date": None,
        "podcast_url": None,
        "transcript": None,
        "transcript_path": None,
        "analysis": None,
        "is_analyzing": False,
        "is_transcribing": False
    }
    st.session_state.update(session_defaults) 