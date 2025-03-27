import streamlit as st
import os
from download import fetch_audio_file

def render_download_section(st):
    """
    Render the download section of the Streamlit interface
    
    Args:
        st: Streamlit object
    """
    url = st.text_input("Enter Xiaoyuzhou podcast URL:")

    if st.button("Start Download"):
        if not url:
            st.warning("Please enter a valid podcast URL")
            return
            
        try:
            # Generate filename from URL
            result = fetch_audio_file(url, None)  # Only get title without actual download
            if result is None:
                st.error("Unable to get podcast information, please check the URL")
                return
                
            audio_path, podcast_title, host_name, publish_date, podcast_url, shownotes = result

            # Execute actual download
            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(progress):
                progress_bar.progress(progress)
                status_text.text(f"Download progress: {int(progress * 100)}%")

            result = fetch_audio_file(url, update_progress)
            if result is None:
                st.error("Download failed, please try again")
                return
                
            audio_path, podcast_title, host_name, publish_date, podcast_url, shownotes = result
            
            st.session_state.update({
                "audio_path": audio_path,
                "podcast_title": podcast_title,
                "podcast_host": host_name,
                "publish_date": publish_date,
                "podcast_url": podcast_url,
                "shownotes": shownotes,
                "download_completed": True
            })
            
            status_text.text("Download completed!")
            st.success(f"Successfully downloaded podcast: {podcast_title}")

        except Exception as e:
            st.error(f"Operation failed: {str(e)}")
            if hasattr(e, '__cause__') and e.__cause__:
                st.error(f"Detailed error: {str(e.__cause__)}") 