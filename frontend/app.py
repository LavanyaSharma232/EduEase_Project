import streamlit as st
import requests
import re
from io import BytesIO
from gtts import gTTS
from typing import Optional, List, Dict # <-- IMPORT THIS

# --- Configuration ---
BACKEND_URL = "https://eduease-project.onrender.com"

# --- Page Configuration and CSS ---
st.set_page_config(page_title="EduEase", page_icon="🧠", layout="wide")
# Your entire CSS block can be pasted here. For brevity, I'm hiding it.
st.markdown("""<style>...</style>""", unsafe_allow_html=True)

# --- UI Helper Functions ---

def parse_graphviz(notes_text: str) -> Optional[str]: # <-- FIX: Corrected return type
    match = re.search(r"```dot\s*([\s\S]+?)\s*```", notes_text)
    if not match: return None
    content = match.group(1).strip()
    if not content.strip().startswith('digraph'): content = f'digraph G {{ {content} }}'
    styling = 'bgcolor="transparent"; node [style="filled", shape="box", fillcolor="#AEC6CF", fontcolor="#121212", color="#FFFFFF", penwidth=2, fontname="Inter"]; edge [color="#FFFFFF", fontname="Inter"];'
    return content.replace('{', f'{{ {styling}', 1)

def highlight_keywords(text: str) -> str:
    # This function is already correct
    colors = ["#FFD6A5", "#FDFFB6", "#CAFFBF", "#9BF6FF", "#FFC0CB"]
    def color_replacer(match):
        keyword = match.group(1)
        color = colors[hash(keyword) % len(colors)]
        return f'<span style="background-color: {color}; ...">{keyword}</span>'
    return re.sub(r"@@(.*?)@@", color_replacer, text)

def find_correct_option(options: List[str], correct_answer: str) -> Optional[int]: # <-- FIX: Corrected types
    # ... (Function content is correct)
    if not options or not correct_answer: return None
    # ... (rest of the function logic)
    return None # Simplified for brevity

def get_topic_from_summary(notes_text: str) -> Optional[str]: # <-- FIX: Corrected return type
    summary_match = re.search(r'##\s*(Detailed\s)?Summary\s*.*?\n(.*?)(?=##)', notes_text, re.DOTALL | re.IGNORECASE)
    if summary_match and summary_match.group(2).strip():
        summary_text = summary_match.group(2).strip()
        # A simple heuristic: take the first N words of the summary
        return " ".join(summary_text.split()[:10])
    return None

# --- Main Streamlit App ---
def app():
    # Logo and Hero Section can be pasted here for brevity
    st.markdown("""<div class="logo-container">...</div>""", unsafe_allow_html=True)
    st.markdown("""<div class="hero-section">...</div>""", unsafe_allow_html=True)

    # --- Session State Initialization ---
    state_keys = {
        "notes": "", "video_url": "", "summary_audio_data": None,
        "mcq_questions": [], "flashcard_questions": [],
        "mcq_current_index": 0, "flashcard_current_index": 0,
        "mcq_answer_submitted": False, "mcq_user_answer": None,
        "processing": False, "learning_level": "Beginner",
        "roadmap_recommendations": None, "topic_title": None,
        "graphviz_data": None
    }
    for key, default_value in state_keys.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

    # --- Input Section ---
    st.markdown("""<div class="input-container">...</div>""", unsafe_allow_html=True)
    
    # FIX: Ensure the label is a proper string
    video_URL = st.text_input(
        label="YouTube Video URL Input",
        placeholder="https://youtube.com/watch?v=...",
        key="video_input",
        label_visibility="collapsed"
    )

    if st.button("📝 Generate Notes", use_container_width=True):
        if video_URL:
            # Reset state for a new URL
            for key, default_value in state_keys.items(): st.session_state[key] = default_value
            st.session_state.video_url = video_URL
            st.session_state.processing = True
            st.rerun()
        else:
            st.warning("Please enter a YouTube URL to get started.", icon="⚠️")
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Features Section ---
    if not st.session_state.notes and not st.session_state.processing:
        st.markdown("""<div class="feature-grid">...</div>""", unsafe_allow_html=True)

    # --- API Calling Logic ---
    if st.session_state.processing:
        with st.spinner('🧙‍♂️ Our AI backend is working its magic...'):
            try:
                generate_url = f"{BACKEND_URL}/generate"
                response = requests.post(generate_url, json={"video_url": st.session_state.video_url}, timeout=600)

                if response.status_code == 200:
                    data = response.json()
                    if data["status"] == "success":
                        # Populate session state from backend's response
                        st.session_state.notes = data.get("notes")
                        st.session_state.mcq_questions = data.get("mcq_questions", [])
                        st.session_state.flashcard_questions = data.get("flashcard_questions", [])
                        st.session_state.graphviz_data = data.get("graphviz_data")

                        # Generate audio summary
                        summary_text = get_topic_from_summary(data.get("notes", "")) # Re-use helper
                        if summary_text:
                            sound_file = BytesIO()
                            tts = gTTS(text=summary_text, lang='en')
                            tts.write_to_fp(sound_file)
                            st.session_state.summary_audio_data = sound_file
                    else:
                        st.error(f"Backend Error: {data.get('message', 'Unknown error')}", icon="🚨")
                else:
                    st.error(f"Connection to backend failed. Status: {response.status_code}", icon="🚨")
            except requests.exceptions.RequestException as e:
                st.error(f"Connection Error: Could not connect to the backend at {BACKEND_URL}. Is it running? Details: {e}", icon="🚨")
            
            st.session_state.processing = False
            st.rerun()

    # --- Display Content ---
    if not st.session_state.processing and st.session_state.notes:
        # The entire display logic (notes, video, quiz, etc.) can be pasted here.
        # It should work without changes as it reads from session_state.
        
        # --- Roadmap Logic ---
        st.markdown("""<div class="input-container" style="max-width: 800px;">...</div>""", unsafe_allow_html=True)
        
        # FIX: Ensure the label is a proper string
        st.session_state.learning_level = st.selectbox(
            label="Select your learning level",
            options=["Beginner", "Intermediate", "Advanced"],
            index=0
        )
        # ... (rest of roadmap logic) ...


# --- Run the App ---
if __name__ == '__main__':
    app()