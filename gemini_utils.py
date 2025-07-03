import google.generativeai as genai
import os
import re
from security_utils import encrypt_text

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Global list to track encrypted sensitive info
sensitive_data_log = []

# 🔐 Mask and encrypt sensitive data from transcribed text
def mask_sensitive_data(text: str) -> str:
    patterns = [
        # 🧾 Financial
        (r'\b(?:\d[ -]*?){13,16}\b', '****CARD****'),                       # Card numbers
        (r'\b\d{4,6}\b', '***PIN***'),                                     # PINs
        (r'\b[A-Z]{4}0[A-Z0-9]{6}\b', '***IFSC***'),                        # IFSC
        (r'\b\d{9,18}\b', '***ACCOUNT***'),                                 # Account Numbers

        # 📞 Contact Info
        (r'\b[6-9]\d{9}\b', '***PHONE***'),                                 # Mobile
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', '***EMAIL***'),  # Email
        (r'\b[\w.\-]{2,256}@[a-z]{2,10}\b', '***UPI***'),                   # UPI ID

        # 🪪 IDs (India)
        (r'\b\d{4}\s?\d{4}\s?\d{4}\b', '***AADHAAR***'),                   # Aadhaar
        (r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', '***PAN***'),                       # PAN
        (r'\b[A-Z]{3}\d{7}\b', '***PASSPORT***'),                          # Passport
        (r'\b\d{2}[A-Z]{3}\d{4}\b', '***VEHICLE***'),                      # Vehicle Reg

        # 🧠 Misc
        (r'\b\d{2}/\d{2}/\d{4}\b', '***DATE***'),                          # Dates
        (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '***IP***'),                      # IP Address
    ]

    def mask_and_store(match, label):
        original = match.group()
        encrypted = encrypt_text(original)
        sensitive_data_log.append((label, encrypted))
        return label

    for regex, label in patterns:
        text = re.sub(regex, lambda m: mask_and_store(m, label), text)

    return text

# 🎙 Main entry: Transcribe, mask/encrypt, and restrict if needed
def transcribe_and_translate(audio_bytes: bytes) -> str:
    global sensitive_data_log
    sensitive_data_log.clear()  # Reset log for this audio

    model = genai.GenerativeModel("models/gemini-2.0-flash")
    response = model.generate_content([
        "You are an AI assistant. Transcribe and translate the given Indian language audio into English.",
        {
            "mime_type": "audio/mp3",
            "data": audio_bytes
        }
    ])

    transcribed = response.text.strip()

    # 🔐 Check for sensitive data
    secured_text = mask_sensitive_data(transcribed)

    if sensitive_data_log:
        print("Sensitive content detected:")
        for label, encrypted in sensitive_data_log:
            print(f"{label}: {encrypted}")
        return "🚫 Please avoid sharing personal or sensitive information like card numbers, PINs, Aadhaar, etc."

    return secured_text
