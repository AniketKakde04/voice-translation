import google.generativeai as genai
import os
import re
from security_utils import encrypt_text

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
sensitive_data_log = []

def mask_sensitive_data(text: str) -> str:
    patterns = [
        # 🧾 Financial Details
        (r'\b(?:\d[ -]*?){13,16}\b', '****CARD****'),                       # Credit/debit card numbers
        (r'\b\d{4,6}\b', '***PIN***'),                                     # 4–6 digit PINs
        (r'\b[A-Z]{4}0[A-Z0-9]{6}\b', '***IFSC***'),                        # IFSC Code
        (r'\b\d{9,18}\b', '***ACCOUNT***'),                                 # Bank account numbers

        # 📞 Contact Details
        (r'\b[6-9]\d{9}\b', '***PHONE***'),                                 # Indian mobile number
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', '***EMAIL***'),  # Email
        (r'\b[\w.\-]{2,256}@[a-z]{2,10}\b', '***UPI***'),                   # UPI ID

        # 🪪 Identity Documents (India)
        (r'\b\d{4}\s?\d{4}\s?\d{4}\b', '***AADHAAR***'),                   # Aadhaar number
        (r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', '***PAN***'),                       # PAN card
        (r'\b[A-Z]{3}\d{7}\b', '***PASSPORT***'),                          # Indian passport
        (r'\b\d{2}[A-Z]{3}\d{4}\b', '***VEHICLE***'),                      # Vehicle number

        # 🧠 Misc
        (r'\b\d{2}/\d{2}/\d{4}\b', '***DATE***'),                          # Date in DD/MM/YYYY
        (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '***IP***'),                      # IPv4 address
    ]

    def mask_and_store(match, label):
        original = match.group()
        encrypted = encrypt_text(original)
        sensitive_data_log.append((label, encrypted))
        return label

    for regex, label in patterns:
        text = re.sub(regex, lambda m: mask_and_store(m, label), text)

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
