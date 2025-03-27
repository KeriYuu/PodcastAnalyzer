import streamlit as st
from openai import OpenAI
from datetime import datetime
import os
import io
from notion_utils import upload_to_notion

# Default system prompt template
DEFAULT_SYSTEM_PROMPT = """你是一名专业的播客内容分析师。请根据Show Notes分析播客内容，并按照指定格式输出分析结果：  

以下是Show Notes：
```
{shownotes}  
```
请按照以下格式输出分析结果，并确保格式完全匹配要求：  

# 内容摘要  
[核心内容总结，限 200 字以内]  

# Show Notes解读（按原结构扩展）
## [原Show Notes标题1]
- 核心观点
- 强化例证（该部分提到的具体案例/数据）
"""

def analyze_podcast_content(transcript: str, api_key: str, system_prompt: str, shownotes: str = "", temperature: float = 0.7) -> str:
    """
    Analyze podcast content using Deepseek-chat model
    
    Args:
        transcript: Podcast transcription text
        api_key: OpenRouter API key
        system_prompt: System prompt template
        shownotes: Podcast shownotes/description
        temperature: Creativity parameter (0.0-1.0)
    
    Returns:
        str: Analysis result
    """
    openai_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    # Format system prompt with shownotes
    formatted_prompt = system_prompt.format(shownotes=shownotes)
    
    messages = [
        {"role": "system", "content": formatted_prompt},
        {"role": "user", "content": "Please analyze the following podcast content:"},
        {"role": "assistant", "content": "I will analyze the podcast content according to the specified format:"},
        {"role": "user", "content": transcript}
    ]
    
    full_response = ""
    for chunk in openai_client.chat.completions.create(
        model="deepseek/deepseek-r1:free",
        messages=messages,
        temperature=temperature,
        stream=True,
        extra_headers={
            "HTTP-Referer": "https://your-domain.com",
            "X-Title": "Podcast Analyzer"
        }
    ):
        if chunk.choices[0].delta.content:
            full_response += chunk.choices[0].delta.content
    
    return full_response

def render_analysis_section(st):
    """
    Optimized interface rendering function
    """
    if st.session_state.transcript:
        st.info("This feature uses the Deepseek-chat model for content analysis")
        
        # ========== Add prompt editing functionality ==========
        with st.container():
            st.write("**Prompt Configuration**")
            system_prompt = st.text_area(
                "System Prompt Template (Editable)",
                value=DEFAULT_SYSTEM_PROMPT,
                height=300,
                help="Modify this prompt to adjust AI's analysis method and output format"
            )
        
        # ========== API Configuration ==========
        with st.container():
            st.write("**API Settings**")
            api_key = st.text_input(
                "OpenRouter API Key",
                type="password",
                help="Get API key from https://openrouter.ai/"
            )
            temperature = st.slider("Creativity Level", 0.0, 1.0, 0.7, 0.1)

        # ========== Notion Configuration ==========
        with st.container():
            st.write("**Notion Settings**")
            notion_token = st.text_input(
                "Notion API Key",
                type="password",
                help="Get from Notion integration settings (starts with secret_)"
            )
            db_id = st.text_input(
                "Notion Database ID",
                help="Get from database URL (e.g., 1234567890abcdef from https://notion.so/workspace/1234567890abcdef)"
            )
        
        # ========== Analysis Button ==========
        if st.button("🧠 Start Smart Analysis", 
                    disabled=(not api_key or st.session_state.is_analyzing),
                    help="API key is required" if not api_key else ""):
            try:
                st.session_state.is_analyzing = True
                
                message_placeholder = st.empty()
                full_response = ""
                
                analysis_result = analyze_podcast_content(
                    st.session_state.transcript,
                    api_key,
                    system_prompt,  # Use user-modified prompt
                    st.session_state.shownotes,
                    temperature
                )
                
                message_placeholder.markdown(analysis_result)
                st.session_state.analysis = analysis_result
                st.success("Analysis completed!")

            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
            finally:
                st.session_state.is_analyzing = False

        # ========== Persistent Analysis Result Display ==========
        if st.session_state.get('analysis'):
            
            # ========== Upload Button ==========
            if notion_token and db_id:
                if st.button("📤 Upload to Notion"):
                    podcast_info = {
                        'title': st.session_state.podcast_title,
                        'host': st.session_state.podcast_host,
                        'date': st.session_state.publish_date,
                        'url': st.session_state.podcast_url
                    }
                    
                    if upload_to_notion(
                        st.session_state.analysis,
                        podcast_info,
                        notion_token,
                        db_id
                    ):
                        st.success("Successfully uploaded to Notion database!")
                st.caption("Ensure: 1. Podcast type is created 2. Database is connected to integration")
            else:
                st.info("Please enter Notion API key and database ID first")

    else:
        st.info("Please complete transcription to get text content first")