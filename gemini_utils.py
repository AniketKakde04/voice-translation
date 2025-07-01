import google.generativeai as genai
import os
import re
from security_utils import encrypt_text

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 🔐 Mask and encrypt sensitive data
def mask_sensitive_data(text: str) -> str:
    card_regex = r'\b(?:\d[ -]*?){13,16}\b'
    pin_regex = r'\b\d{4,6}\b'

    def replace_with_encryption(match):
        original = match.group()
        encrypted = encrypt_text(original)
        return f"[ENCRYPTED:{encrypted}]"

    text = re.sub(card_regex, replace_with_encryption, text)
    text = re.sub(pin_regex, replace_with_encryption, text)
    return text

# 🎙 Transcribe and translate audio, then secure sensitive info
def transcribe_and_translate(audio_bytes: bytes) -> str:
    model = genai.GenerativeModel("models/gemini-2.0-flash")

    response = model.generate_content([
        "You are an AI assistant. Transcribe and translate the given Indian language audio into English.",
        {
            "mime_type": "audio/mp3",
            "data": audio_bytes
        }
    ])

    transcribed = response.text.strip()
    secured = mask_sensitive_data(transcribed)
    return secured
