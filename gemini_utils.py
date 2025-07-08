import google.generativeai as genai
import os
import re
from security_utils import encrypt_text
from supabase_utils import add_sensitive_value, get_all_sensitive_values, log_translation

# Setup Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Holds encrypted sensitive items per request
sensitive_data_log = []

# Known regex patterns
known_patterns = [
    (r'\b(?:\d[ -]*?){13,16}\b', '****CARD****'),
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

    # Step 1: Mask known patterns
    for regex, label in known_patterns:
        text = re.sub(regex, lambda m: mask_and_store(m, label), text)

    # Step 2: Mask based on Supabase stored values
    stored = get_all_sensitive_values()
    for label, value in stored:
        if value in text:
            encrypted = encrypt_text(value)
            text = text.replace(value, label)
            sensitive_data_log.append((label, encrypted))

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
    result = response.text.strip()

    try:
        import json
        sensitive_items = json.loads(result)
        for item in sensitive_items:
            if item in text:
                encrypted = encrypt_text(item)
                label = '***UNKNOWN***'
                text = text.replace(item, label)
                sensitive_data_log.append((label, encrypted))

                # Store to Supabase for future use
                add_sensitive_value(label, item)

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

    # Step 1: Apply regex and stored DB values
    partially_masked = mask_sensitive_data(translated)

    # Step 2: Detect unknown sensitive info via Gemini
    fully_masked = detect_unknown_sensitive_info(partially_masked)

    # Step 3: Log the full translation to Supabase
    log_translation(original_text=translated, masked_text=fully_masked)

    # Step 4: Return message
    if sensitive_data_log:
        return f"""📝 {fully_masked}
⚠️ Sensitive info was encrypted for your safety."""
    return fully_masked
