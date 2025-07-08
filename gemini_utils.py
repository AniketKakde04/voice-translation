import google.generativeai as genai
import os
import re
from security_utils import encrypt_text

# Setup Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Stores encrypted sensitive items
sensitive_data_log = []

# Known regex patterns
known_patterns = [
    (r'\b(?:\d[ -]*?){13,16}\b', '****CARD****'),     # Card numbers
    (r'\b\d{4,6}\b', '***PIN***'),
    (r'\b[A-Z]{4}0[A-Z0-9]{6}\b', '***IFSC***'),
    (r'\b\d{9,18}\b', '***ACCOUNT***'),
    (r'\b[6-9]\d{9}\b', '***PHONE***'),
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', '***EMAIL***'),
    (r'\b[\w.\-]{2,256}@[a-z]{2,10}\b', '***UPI***'),
    (r'\b\d{4}\s?\d{4}\s?\d{4}\b', '***AADHAAR***'),
    (r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', '***PAN***'),
    (r'\b[A-Z]{3}\d{7}\b', '***PASSPORT***'),
    (r'\b\d{2}[A-Z]{3}\d{4}\b', '***VEHICLE***'),
    (r'\b\d{2}/\d{2}/\d{4}\b', '***DATE***'),
    (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '***IP***'),
]

def mask_sensitive_data(text: str) -> str:
    def mask_and_store(match, label):
        original = match.group()
        encrypted = encrypt_text(original)
        sensitive_data_log.append((label, encrypted))
        return label

    for regex, label in known_patterns:
        text = re.sub(regex, lambda m: mask_and_store(m, label), text)

    return text

def detect_unknown_sensitive_info(text: str) -> str:
    model = genai.GenerativeModel("models/gemini-2.0")
    prompt = f"""
Your task is to detect any personal or sensitive information in the following message that may have been missed by traditional patterns like card numbers, phone numbers, emails, etc. 
Only return a JSON list of the exact values you believe are sensitive, without explanation.

Message:
{text}
"""

    response = model.generate_content(prompt)
    found = response.text.strip()

    # Expecting a list of strings
    try:
        import json
        sensitive_items = json.loads(found)
        for item in sensitive_items:
            if item in text:
                encrypted = encrypt_text(item)
                label = '***UNKNOWN***'
                text = text.replace(item, label)
                sensitive_data_log.append((label, encrypted))

    except Exception as e:
        print("Failed to parse Gemini response:", e)

    return text

def transcribe_and_translate(audio_bytes: bytes) -> str:
    global sensitive_data_log
    sensitive_data_log.clear()

    model = genai.GenerativeModel("models/gemini-2.0-flash")
    response = model.generate_content([
        "You are an AI assistant. The user will send you a voice note in an Indian language. Do not transcribe it. Only return the English translation.",
        {
            "mime_type": "audio/mp3",
            "data": audio_bytes
        }
    ])

    translated = response.text.strip()

    # Step 1: Mask known sensitive data
    masked_text = mask_sensitive_data(translated)

    # Step 2: Detect and mask unknown sensitive data
    final_text = detect_unknown_sensitive_info(masked_text)

    if sensitive_data_log:
        return f"""📝 {final_text}
⚠️ Sensitive info was encrypted for your safety."""
    return final_text
