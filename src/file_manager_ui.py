import streamlit as st
import os
import time

def render_file_manager_section(st):
    """
    Render the file management section of the Streamlit interface
    
    Args:
        st: Streamlit object
    """
    if not st.session_state.download_completed:
        return
        
    # File information display
    with st.container():
        st.write("**Current File List:**")
        st.write("**Audio File**")
        st.code(st.session_state.audio_path)

    # Delete functionality
    st.write("**Danger Zone**")
    if st.button("🗑️ Delete Audio File", type="primary"):
        try:
            deleted_files = []
            # Delete audio file
            if os.path.exists(st.session_state.audio_path):
                os.remove(st.session_state.audio_path)
                deleted_files.append(f"Audio file: {st.session_state.audio_path}")
            
            # Reset state
            st.session_state.update({
                "download_completed": False,
                "audio_path": None,
                "podcast_title": None,
                "is_transcribing": False
            })
            
            # Display results
            if deleted_files:
                st.success("The following files have been successfully deleted:")
                for f in deleted_files:
                    st.write(f"`{f}`")
                st.balloons()
                time.sleep(1)
                st.rerun()
            else:
                st.info("No files found to delete")
                
        except PermissionError:
            st.error("Delete failed: File is being used by another program")
        except Exception as e:
            st.error(f"Error occurred during deletion: {str(e)}") 