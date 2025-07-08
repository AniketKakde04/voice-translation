import os
import re
import google.generativeai as genai
from nltk.tokenize import sent_tokenize
from shared_state import sensitive_data_log
from security_utils import encrypt_text
from supabase_utils import add_sensitive_value, get_all_sensitive_values, log_translation
from rag_utils import rag_detect_and_store

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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

# ✅ Regex-based + DB masking
def mask_sensitive_data(text: str) -> str:
    def mask_and_store(match, label):
        original = match.group()
        encrypted = encrypt_text(original)
        sensitive_data_log.append((label, encrypted))
        return label

    for regex, label in known_patterns:
        text = re.sub(regex, lambda m: mask_and_store(m, label), text)

    stored_values = get_all_sensitive_values()
    for label, value in stored_values:
        if value in text:
            encrypted = encrypt_text(value)
            text = text.replace(value, label)
            sensitive_data_log.append((label, encrypted))

    return text

# ✅ RAG detection for unknown sensitive values
def detect_unknown_sensitive_info(text: str) -> str:
    chunks = sent_tokenize(text)
    for chunk in chunks:
        masked = rag_detect_and_store(chunk)
        if masked != chunk:
            text = text.replace(chunk, masked)
    return text

# ✅ Full transcribe + translate pipeline
def transcribe_and_translate(audio_bytes: bytes) -> str:
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

    masked_text = mask_sensitive_data(translated)
    final_text = detect_unknown_sensitive_info(masked_text)

    log_translation(translated, final_text)

    if sensitive_data_log:
        return f"""📝 {final_text}
⚠️ Sensitive info was encrypted for your safety."""
    return final_text
