import os
import re
import json
import logging
from dotenv import load_dotenv
from typing import Optional, List, Dict # <-- IMPORT THIS FOR TYPE HINTING

# --- Corrected Google Imports ---
# We will explicitly import the components to make Pylance happy
from google.generativeai.client import configure
from google.generativeai.generative_models import  GenerativeModel

from googleapiclient.discovery import build
# --- End of Corrected Imports ---

from faster_whisper import WhisperModel
import yt_dlp

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Load Environment Variables and Configure APIs ---
try:
    load_dotenv()
    
    # Configure Google AI (Gemini)
    gemini_api_key = os.getenv("GOOGLE_API_KEY")
    if not gemini_api_key:
        raise ValueError("GOOGLE_API_KEY not found. Make sure it's in your .env file.")
    # Now we call the directly imported function
    configure(api_key=gemini_api_key)
    logging.info("Successfully configured Google AI (Gemini) API key.")

    # Prepare the YouTube API client
    youtube_api_key = os.getenv("YOUTUBE_API_KEY", gemini_api_key)
    if not youtube_api_key:
        logging.warning("YOUTUBE_API_KEY not found. Roadmap generation may fail.")
        youtube_service = None
    else:
        youtube_service = build('youtube', 'v3', developerKey=youtube_api_key)
        logging.info("Successfully configured YouTube Data API client.")

except Exception as e:
    logging.critical(f"Failed to configure APIs on startup: {e}")
    raise SystemExit(f"Could not configure essential APIs, cannot run. Error: {e}")

# --- Core Processing Functions ---

def video_to_audio(video_url: str, output_path: str = "Target_audio.mp3") -> str:
    # ... (This function is already correct)
    logging.info(f"Starting audio extraction for URL: {video_url}")
    # ... (rest of the function code)
    unique_id = os.path.basename(output_path).split('.')[0]
    output_template = f"{unique_id}.%(ext)s"

    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': output_template,
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192',}],
        'postprocessor_args': ['-ar', '16000', '-ac', '1'],
        'prefer_ffmpeg': True, 'keepvideo': False, 'noplaylist': True, 'quiet': True, 'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise FileNotFoundError("Audio file was not created or is empty.")
        logging.info(f"Audio extracted successfully to {output_path}")
        return output_path
    except Exception as e:
        logging.error(f"yt-dlp failed for URL {video_url}. Error: {e}")
        raise e

def audio_to_text(audio_path: str) -> str:
    # ... (This function is already correct)
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found at path: {audio_path}")
    try:
        logging.info(f"Loading Whisper model for transcription of {audio_path}.")
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(audio_path, beam_size=5)
        transcript = "".join(segment.text for segment in segments)
        logging.info(f"Transcription complete. Transcript length: {len(transcript)} characters.")
        return transcript
    except Exception as e:
        logging.error(f"Whisper transcription failed for {audio_path}. Error: {e}")
        raise e

def generate_notes(text: str) -> str:
    """Generates structured study notes from a transcript using the Gemini AI model."""
    logging.info("Calling Gemini API to generate notes.")
    if not text:
        raise ValueError("Cannot generate notes from an empty transcript.")

    system_prompt = """...""" # Your long prompt here

    try:
        # Now we call the directly imported class
        model = GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content(system_prompt + "\n\nHere is the transcript:\n" + text)
        
        if not response or not hasattr(response, 'text') or not response.text:
            raise ValueError("Gemini API returned an empty or malformed response.")
            
        logging.info("Successfully generated notes from Gemini API.")
        return response.text

    except Exception as e:
        logging.error(f"Gemini API call for notes generation failed: {e}")
        raise e

# --- Parsing and Utility Functions ---

def parse_graphviz(notes_text: str) -> Optional[str]: # <-- FIX: Changed return type
    """Parses Graphviz 'dot' data from notes for display."""
    # ... (Function content is correct)
    match = re.search(r"```dot\s*([\s\S]+?)\s*```", notes_text)
    if not match: 
        return None
    content = match.group(1).strip()
    if not content.strip().startswith('digraph'): 
        content = f'digraph G {{ {content} }}'
    styling = 'bgcolor="transparent"; node [style="filled", shape="box", fillcolor="#AEC6CF", fontcolor="#121212", color="#FFFFFF", penwidth=2, fontname="Inter"]; edge [color="#FFFFFF", fontname="Inter"];'
    return content.replace('{', f'{{ {styling}', 1)


def parse_quiz_from_json(notes_text: str, key: str) -> List[Dict]: # <-- FIX: More specific type
    """Parses a specific JSON block (like for a quiz) from the notes text."""
    # ... (Function content is correct)
    pattern = re.compile(f'##\\s*{key}[\\s\\S]*?```json\\s*([\\s\\S]+?)\\s*```', re.IGNORECASE)
    match = pattern.search(notes_text)
    if not match: 
        return []
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        logging.warning(f"Failed to parse JSON for key: '{key}'")
        return []


def get_topic_from_summary(notes_text: str) -> Optional[str]: # <-- FIX: Changed return type
    """Extracts the summary from notes and uses AI to distill a concise search topic."""
    # ... (Function content is correct)
    logging.info("Distilling topic from summary.")
    summary_match = re.search(r'##\s*(Detailed\s)?Summary\s*.*?\n(.*?)(?=##)', notes_text, re.DOTALL | re.IGNORECASE)
    
    if not summary_match or not summary_match.group(2).strip():
        logging.warning("Could not find a summary in the notes to generate a topic from.")
        return None
        
    summary_text = summary_match.group(2).strip()

    try:
        model = GenerativeModel('gemini-1.5-flash-latest')
        prompt = (f"Based on the following summary... ") # Your short topic prompt
        
        response = model.generate_content(prompt)
        
        if response and hasattr(response, 'text') and response.text:
            topic = response.text.strip().replace('"', '')
            logging.info(f"Successfully distilled topic: '{topic}'")
            return topic
        else:
            raise ValueError("Gemini API returned an empty response for topic distillation.")
            
    except Exception as e:
        logging.error(f"Gemini API call for topic distillation failed: {e}")
        return None


def get_youtube_recommendations(topic: str, level: str, max_results: int = 3) -> List[Dict]: # <-- FIX: More specific type
    """Fetches YouTube video recommendations based on a topic and learning level."""
    # ... (Function content is correct)
    if not youtube_service:
        logging.warning("YouTube service not available. Skipping recommendations.")
        return []
    if not topic:
        logging.warning("No topic provided. Skipping recommendations.")
        return []

    logging.info(f"Fetching YouTube recommendations for topic: '{topic}', level: '{level}'.")
    query = f"{topic} for {level}s tutorial"

    try:
        search_response = youtube_service.search().list(q=query, part='snippet', maxResults=max_results, type='video').execute()

        recommendations = []
        for item in search_response.get('items', []):
            recommendations.append({
                "title": item['snippet']['title'],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                "thumbnail": item['snippet']['thumbnails']['high']['url']
            })
        logging.info(f"Found {len(recommendations)} YouTube recommendations.")
        return recommendations
    except Exception as e:
        logging.error(f"YouTube API search failed: {e}")
        return []