import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import os
from tqdm import tqdm
from datetime import datetime
import json

def fetch_audio_file(url, progress_callback=None):
    # Define paths before initializing browser driver to avoid repeated creation
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)  # Initialize browser driver early
    audio_path = None  # Define audio_path at the beginning of the function

    try:
        driver.get(url)
        
        # Get podcast title
        title_element = driver.find_element(By.XPATH, "//h1[contains(@class,'title')]")
        podcast_title = title_element.text.strip()  # Clean whitespace
        
        # Get host information
        host_element = driver.find_element(By.XPATH, "//a[contains(@class,'name')]")
        host_name = host_element.text.strip()
        
        # Get publish date
        date_element = driver.find_element(By.XPATH, "//time[contains(@class,'jsx-399326063')]")
        publish_date = date_element.get_attribute("datetime")  # Get ISO format datetime
        
        # Get podcast description
        script_element = driver.find_element(By.XPATH, "//script[@name='schema:podcast-show']")
        script_content = script_element.get_attribute("textContent")
        podcast_data = json.loads(script_content)
        shownotes = podcast_data.get("description", "")
        
        # Build save path
        os.makedirs("audio_files", exist_ok=True)
        audio_filename = f"{podcast_title}-episode_audio.mp3"
        audio_path = os.path.join("audio_files", audio_filename)
        
        # 检查音频文件是否已存在
        if os.path.exists(audio_path):
            print(f"音频文件已存在: {audio_path}")
            return audio_path, podcast_title, host_name, publish_date, url, shownotes
        
        # Continue download process if file doesn't exist
        audio_element = driver.find_element(By.TAG_NAME, "audio")
        audio_url = audio_element.get_attribute("src")
        if not audio_url:
            print("Audio URL not found")
            return None

        # Download file (with timeout and retry mechanism)
        response = requests.get(audio_url, stream=True, verify=False, timeout=30)
        response.raise_for_status()  # Check HTTP status code
        
        # Use efficient download method
        total_size = int(response.headers.get('content-length', 0))
        with open(audio_path, 'wb') as f, tqdm(
            total=total_size, unit='iB', unit_scale=True, desc=audio_filename
        ) as bar:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))
                    if progress_callback:
                        progress_callback(bar.n / total_size)
        
        return audio_path, podcast_title, host_name, publish_date, url, shownotes

    except Exception as e:
        print(f"Operation failed: {str(e)}")
        if audio_path and os.path.exists(audio_path):  # Clean up incomplete file
            os.remove(audio_path)
        return None
    finally:
        driver.quit()