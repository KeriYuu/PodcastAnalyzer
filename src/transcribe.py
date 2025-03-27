import argparse
import os
import subprocess
from datetime import timedelta
from pathlib import Path
import time

import filetype
import requests
from faster_whisper import WhisperModel
from pydub import AudioSegment
from tqdm import tqdm

# 初始化配置
SUPPORTED_API_FORMATS = ['flac', 'm4a', 'mp3', 'mp4', 'mpeg', 'mpga', 'oga', 'ogg', 'wav', 'webm']
MAX_API_SIZE = 100 * 1024 * 1024  # 调整为更大的文件限制（可选）

def format_timestamp(seconds):
    """将秒转换为SRT时间格式：HH:MM:SS,mmm"""
    millisec = int((seconds - int(seconds)) * 1000)
    return str(timedelta(seconds=int(seconds))) + f",{millisec:03d}"

def generate_srt(segments):
    """将转录片段转换为SRT格式"""
    srt = []
    for i, segment in enumerate(segments, start=1):
        start_time = format_timestamp(segment.start)
        end_time = format_timestamp(segment.end)
        text = segment.text.strip()
        srt.append(f"{i}\n{start_time} --> {end_time}\n{text}\n")
    return "\n".join(srt)

def generate_txt(segments):
    """将转录片段转换为纯文本"""
    return "\n".join(segment.text.strip() for segment in segments)

def get_audio_duration(file_path):
    """使用ffprobe获取音频时长（秒）"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return float(result.stdout.strip())

def validate_audio_file(file_path):
    """深度验证音频文件完整性"""
    try:
        kind = filetype.guess(file_path)
        if not kind or kind.mime.split('/')[0] != 'audio':
            raise ValueError("无效的音频文件")
        
        subprocess.run(
            ["ffmpeg", "-v", "error", "-i", file_path, "-f", "null", "-"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True
    except Exception as e:
        raise ValueError(f"文件验证失败: {str(e)}") from e

def convert_to_supported_format(input_path):
    """智能音频格式转换（带错误修复）"""
    output_path = Path(input_path).with_suffix(".mp3")
    
    try:
        subprocess.run(
            ["ffmpeg", "-i", input_path, "-c:a", "copy", output_path],
            check=True, stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError:
        subprocess.run(
            ["ffmpeg", "-i", input_path, "-c:a", "libmp3lame", "-q:a", "2", output_path],
            check=True
        )
    
    validate_audio_file(output_path)
    return output_path

def transcribe_audio(audio_path, output_file, output_format="txt", device_option='cpu', 
                    mode='local', api_url=None, progress_callback=None):
    """
    Enhanced audio transcription function
    """
    output_dir = "transcript_files"
    output_path = os.path.join(output_dir, output_file)
    
    print(f"Starting processing: {audio_path}")
    
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # Check if transcript file already exists
    if os.path.exists(output_path):
        print(f"Transcript file exists: {output_path}")
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Failed to load existing transcript: {str(e)}")
            # If loading fails, continue with new transcription
    
    # If no progress callback is provided, just get info
    if progress_callback is None:
        return output_path, output_file, output_format, mode, api_url
    
    try:
        if mode == 'api':
            file_type = filetype.guess(audio_path)
            if not file_type:
                raise ValueError("Unable to identify file type")
                
            print(f"Actual file type: {file_type.extension} (MIME: {file_type.mime})")

            if file_type.extension not in SUPPORTED_API_FORMATS:
                raise ValueError(f"File type {file_type.extension} not in supported list")

            if not api_url:
                raise ValueError("API mode requires server URL")
            
            if progress_callback:
                progress_callback(0.1, "Converting audio format...")
            converted_path = convert_to_supported_format(audio_path) if file_type.extension != 'mp3' else audio_path

            format_mapping = {
                "txt": "text",
                "srt": "srt",
                "vtt": "vtt",
                "json": "json"
            }
            
            response_format = format_mapping.get(output_format.lower(), 'text')

            try:
                with open(converted_path, 'rb') as f:
                    files = {'file': f}
                    data = {'response_format': response_format}
                    
                    if progress_callback:
                        progress_callback(0.3, "Transcribing...")
                    
                    response = requests.post(
                        api_url,
                        files=files,
                        data=data,
                        timeout=60
                    )
                    response.raise_for_status()

                if response_format == 'srt':
                    final_content = response.text
                else:
                    final_content = response.json().get('text', '')
            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"API request failed: {str(e)}")
            
            if converted_path != audio_path:
                Path(converted_path).unlink()
                
        else:
            device = device_option or 'cpu'
            compute_type = "float16" if device == "cuda" else "int8"
            
            if progress_callback:
                progress_callback(0.1, "Loading Whisper model...")
            model = WhisperModel("base", device=device, compute_type=compute_type)
            
            if progress_callback:
                progress_callback(0.2, "Starting transcription...")
            
            duration = get_audio_duration(audio_path)
            start_time = time.time()
            
            segments, info = model.transcribe(audio_path, beam_size=5)
            
            processed_segments = []
            for segment in segments:
                processed_segments.append(segment)
                if progress_callback:
                    elapsed_time = time.time() - start_time
                    progress = min(0.2 + (0.7 * (elapsed_time / duration)), 0.9)
                    progress_callback(progress, f"Transcribing... ({int(elapsed_time)}s / {int(duration)}s)")
            
            if progress_callback:
                progress_callback(0.9, "Processing transcription results...")
            
            print(f"Detected language: {info.language} (confidence: {info.language_probability:.2f})")
            final_content = generate_srt(processed_segments) if output_format.lower() == "srt" else generate_txt(processed_segments)

        if progress_callback:
            progress_callback(1.0, "Saving transcript file...")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_content)
        
        print(f"Successfully saved to: {output_path}")
        return final_content
    
    except Exception as e:
        if os.path.exists(output_path):
            os.remove(output_path)
        error_msg = f"Transcription failed: {str(e)}"
        
        if "Invalid file format" in str(e):
            actual_type = filetype.guess(audio_path)
            error_msg += f"\nFile diagnostics:\n- Extension: {Path(audio_path).suffix}\n- Actual type: {actual_type.extension if actual_type else 'unknown'}"
        
        print(error_msg)
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="音频转录工具")
    parser.add_argument("-i", "--input", required=True, help="输入音频文件路径")
    parser.add_argument("-o", "--output", default="transcription_output.txt", help="输出文件路径")
    parser.add_argument("-f", "--format", choices=["txt", "srt"], default="txt", help="输出格式")
    parser.add_argument("-d", "--device", default=None, help="运行设备 (cpu/cuda)")
    parser.add_argument("-m", "--mode", choices=["local", "api"], default="local", help="转录模式")
    parser.add_argument("--api-url", help="自托管服务器URL (API模式必需)")
    
    args = parser.parse_args()
    
    transcribe_audio(
        args.input,
        args.output,
        args.format,
        args.device,
        args.mode,
        args.api_url
    )