import os
import uuid
import chromadb
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

from shared_state import sensitive_data_log
from security_utils import encrypt_text
from supabase_utils import add_sensitive_value

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Chroma setup
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="sensitive_chunks")

# Embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# ✅ Store a sensitive phrase in Chroma
def store_sensitive_phrase(phrase: str):
    embedding = model.encode(phrase).tolist()
    collection.add(
        documents=[phrase],
        embeddings=[embedding],
        ids=[str(uuid.uuid4())]
    )

# ✅ Check if phrase is sensitive using RAG + Gemini
def is_phrase_sensitive(phrase: str) -> bool:
    embedding = model.encode(phrase).tolist()
    results = collection.query(query_embeddings=[embedding], n_results=5)

    if not results["documents"] or not results["documents"][0]:
        return False

    context = "\n".join(results["documents"][0])
    prompt = (
        "You are a data privacy assistant. Based on these past sensitive examples:\n\n"
        f"{context}\n\n"
        f'Is the following sentence sensitive or personal and should it be masked?\n\n'
        f'Sentence: "{phrase}"\n\n'
        "Reply only with 'Yes' or 'No'."
    )

    response = genai.GenerativeModel("models/gemini-2.0").generate_content(prompt)
    answer = response.text.strip().lower()

    print(f"RAG check: {phrase}")
    print(f"Similar examples:\n{context}")
    print(f"Gemini said: {answer}")

    return answer.startswith("yes")

# ✅ Main function to detect, store & mask
def rag_detect_and_store(phrase: str) -> str:
    if is_phrase_sensitive(phrase):
        encrypted = encrypt_text(phrase)
        label = "***UNKNOWN***"
        sensitive_data_log.append((label, encrypted))
        add_sensitive_value(label, phrase)
        store_sensitive_phrase(phrase)
        return label

    return phrase
