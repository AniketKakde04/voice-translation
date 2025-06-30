import google.generativeai as genai
import base64

import os
from io import BytesIO

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def transcribe_and_translate(audio_bytes: bytes) -> str:
    model = genai.GenerativeModel("models/gemini-1.5-flash-latest")

    # Gemini expects audio in WAV or MP3 or OGG – use directly
    response = model.generate_content([
        "You are an AI assistant. Transcribe and translate the given Indian language audio into English.",
        {
            "mime_type": "audio/mp3",
            "data": audio_bytes
        }
    ])

    return response.text.strip()
