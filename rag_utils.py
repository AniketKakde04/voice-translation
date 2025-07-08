import os
import uuid
import chromadb
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

from gemini_utils import sensitive_data_log
from security_utils import encrypt_text
from supabase_utils import add_sensitive_value

# Setup Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Chroma setup (in-memory or persistent)
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="sensitive_chunks")

# Sentence embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")  # Lightweight and fast

# ✅ Store a new sensitive phrase (embedding + vector DB)
def store_sensitive_phrase(phrase: str):
    embedding = model.encode(phrase).tolist()
    collection.add(
        documents=[phrase],
        embeddings=[embedding],
        ids=[str(uuid.uuid4())]  # Ensure unique ID
    )

# ✅ Check if a phrase looks sensitive using retrieval + Gemini
def is_phrase_sensitive(phrase: str) -> bool:
    embedding = model.encode(phrase).tolist()
    results = collection.query(query_embeddings=[embedding], n_results=5)

    # Skip if no context
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

    # Debug (optional)
    print(f"RAG check for: {phrase}")
    print(f"Context examples:\n{context}")
    print(f"Gemini response: {answer}")

    return answer.startswith("yes")

# ✅ Main function to run full RAG-sensitive detection
def rag_detect_and_store(phrase: str) -> str:
    if is_phrase_sensitive(phrase):
        encrypted = encrypt_text(phrase)
        label = "***UNKNOWN***"
        sensitive_data_log.append((label, encrypted))

        # Store in Supabase + Chroma
        add_sensitive_value(label, phrase)
        store_sensitive_phrase(phrase)

        return label

    return phrase
