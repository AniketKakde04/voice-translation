import os
import requests
from security_utils import encrypt_text, decrypt_text
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ✅ Store encrypted sensitive value
def add_sensitive_value(label: str, plain_value: str):
    encrypted_value = encrypt_text(plain_value)
    payload = {
        "label": label,
        "encrypted_value": encrypted_value
    }
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/sensitive_values",
        headers=HEADERS,
        json=payload
    )
    response.raise_for_status()

# ✅ Fetch all stored sensitive values (decrypted)
def get_all_sensitive_values():
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/sensitive_values",
        headers=HEADERS
    )
    response.raise_for_status()
    rows = response.json()
    return [(row["label"], decrypt_text(row["encrypted_value"])) for row in rows]

# ✅ Log translation result
def log_translation(original_text: str, masked_text: str):
    payload = {
        "original_translated_text": original_text,
        "final_secured_text": masked_text
    }
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/translations",
        headers=HEADERS,
        json=payload
    )
    response.raise_for_status()
