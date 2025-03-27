import os
# Set environment variables to resolve OpenMP duplicate loading issue
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'

import time
from pathlib import Path
from dotenv import load_dotenv
from download import fetch_audio_file
from transcribe import transcribe_audio
from analyze import analyze_podcast_content, DEFAULT_SYSTEM_PROMPT
from notion_utils import upload_to_notion
from tqdm import tqdm
import psutil
import signal

def read_podcast_urls():
    urls = []
    with open('podcast_urls.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'): 
                urls.append(line)
    return urls

def process_podcast(url):
    try:
        print(f"\nStart processing {url}")
        
        progress_bar = tqdm(total=100, desc="Processing progress", unit="%")
        
        def update_progress(progress, message=None):
            progress_bar.set_description(message if message else "Processing progress")
            progress_bar.n = int(progress * 100)
            progress_bar.refresh()
        
        # Use requests method for background processing
        result = fetch_audio_file(url, progress_callback=lambda p: update_progress(p * 0.3, "Downloading audio"))
        if not result:
            print(f"{url} failed to download")
            return False
            
        audio_path, podcast_title, host_name, publish_date, podcast_url, shownotes = result
        print(f"{podcast_title} downloaded")
        
        # Use the same filename format as UI version
        output_format = os.getenv('OUTPUT_FORMAT', 'txt')
        output_file = f"{podcast_title}.{output_format}"
        
        # First get transcription info
        result = transcribe_audio(
            audio_path,
            output_file,
            output_format=output_format,
            device_option=os.getenv('DEVICE_OPTION', 'cpu'),
            mode=os.getenv('TRANSCRIBE_MODE', 'local'),
            progress_callback=None  # No progress callback, just get info
        )
        
        # If result is a tuple, file doesn't exist, need to perform actual transcription
        if isinstance(result, tuple):
            transcribe_audio(
                audio_path,
                output_file,
                output_format=output_format,
                device_option=os.getenv('DEVICE_OPTION', 'cpu'),
                mode=os.getenv('TRANSCRIBE_MODE', 'local'),
                progress_callback=lambda p, m: update_progress(0.3 + p * 0.4, m)
            )
            print(f"{output_file} transcribed")
        else:
            print(f"Using existing transcript: {output_file}")
            transcript = result
            update_progress(0.7, "Using existing transcript")
        
        update_progress(0.7, "Analyzing content")
        with open(os.path.join('transcript_files', output_file), 'r', encoding='utf-8') as f:
            transcript = f.read()
            
        analysis = analyze_podcast_content(
            transcript=transcript,
            api_key=os.getenv('OPENROUTER_API_KEY'),
            system_prompt=DEFAULT_SYSTEM_PROMPT,  # Use default system prompt template
            shownotes=shownotes,
            temperature=0.7  # Use default temperature value
        )
        print("Content analyzed")
        
        update_progress(0.8, "Uploading to Notion")
        podcast_info = {
            'title': podcast_title,
            'host': host_name,
            'date': publish_date,
            'url': podcast_url
        }
        
        if upload_to_notion(
            analysis,
            podcast_info,
            os.getenv('NOTION_TOKEN'),
            os.getenv('NOTION_DATABASE_ID')
        ):
            update_progress(1.0, "Uploaded to Notion successfully")
            return True
        else:
            print("Upload to Notion failed")
            return False
            
    except Exception as e:
        print(f"Processing failed: {str(e)}")
        return False
    finally:
        progress_bar.close()
        # Add a delay before processing the next podcast
        time.sleep(2)

def main():
    load_dotenv()
    
    # Check required environment variables
    required_vars = ['OPENROUTER_API_KEY', 'NOTION_TOKEN', 'NOTION_DATABASE_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        return
    
    
    urls = read_podcast_urls()
    if not urls:
        print("Error: podcast_urls.txt has no valid URLs")
        return
    
    success_count = 0
    total_count = len(urls)
    
    print(f"\nProcessing {total_count} podcasts...")
    for i, url in enumerate(urls, 1):
        print(f"\nProcessing podcast {i}/{total_count}")
        if process_podcast(url):
            success_count += 1
        # Add a delay between podcasts
        if i < total_count:
            print("Waiting before processing next podcast...")
            time.sleep(3)
    
    print(f"\nProcessing completed! Success: {success_count}/{total_count}")

if __name__ == "__main__":
    main() 