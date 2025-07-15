# backend/main.py

import os  # <-- ADD THIS IMPORT
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import processing # Import our helper functions

app = FastAPI()

# --- CORS Middleware ---
# This is CRUCIAL to allow your Streamlit frontend
# to communicate with this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request and Response Models ---
class VideoRequest(BaseModel):
    video_url: str

class RoadmapRequest(BaseModel):
    topic: str
    level: str

# --- API Endpoints ---
@app.post("/generate")
def generate_notes_endpoint(request: VideoRequest):
    """
    This endpoint takes a YouTube URL, runs the full processing pipeline,
    and returns all the generated content.
    """
    audio_file_path = "Target_audio.mp3"
    try:
        # 1. Process Video
        processing.video_to_audio(request.video_url, audio_file_path)
        transcript = processing.audio_to_text(audio_file_path)

        # 2. Generate Notes & Topic
        notes_text = processing.generate_notes(transcript)
        
        # 3. Parse Content
        mcq_questions = processing.parse_quiz_from_json(notes_text, key="MCQ Quiz")
        flashcard_questions = processing.parse_quiz_from_json(notes_text, key="Flashcard Review")
        graphviz_data = processing.parse_graphviz(notes_text)

        # 5. Return everything in a JSON response
        return {
            "status": "success",
            "notes": notes_text,
            "mcq_questions": mcq_questions,
            "flashcard_questions": flashcard_questions,
            "graphviz_data": graphviz_data
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        # 4. Clean up the audio file in all cases (success or error)
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)

@app.post("/roadmap")
def generate_roadmap_endpoint(request: RoadmapRequest):
    """
    This endpoint takes a topic and level and returns video recommendations.
    """
    try:
        recommendations = processing.get_youtube_recommendations(
            topic=request.topic, 
            level=request.level
        )
        return {"status": "success", "recommendations": recommendations}
    except Exception as e:
        return {"status": "error", "message": str(e)}