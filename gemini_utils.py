import google.generativeai as genai
import os
import re
from security_utils import encrypt_text

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
sensitive_data_log = []

def mask_sensitive_data(text: str) -> str:
    card_regex = r'\b(?:\d[ -]*?){13,16}\b'
    pin_regex = r'\b\d{4,6}\b'

    def mask_and_store(match, label="****"):
        original = match.group()
        encrypted = encrypt_text(original)
        sensitive_data_log.append((label, encrypted))
        return label

    # Replace card numbers with '****'
    text = re.sub(card_regex, lambda m: mask_and_store(m, "****"), text)

    # Replace 4–6 digit PINs with '***PIN***'
    text = re.sub(pin_regex, lambda m: mask_and_store(m, "***PIN***"), text)

    return text
# 🎙 Transcribe and translate audio, then secure sensitive info
def transcribe_and_translate(audio_bytes: bytes) -> str:
    model = genai.GenerativeModel("models/gemini-2.0-flash")

    response = model.generate_content([
        "You are an AI assistant. Transcribe and translate the given Indian language audio into English and just provide the converted english text",
        {
            "mime_type": "audio/mp3",
            "data": audio_bytes
        }
    ])

    transcribed = response.text.strip()
    secured = mask_sensitive_data(transcribed)
    return secured
