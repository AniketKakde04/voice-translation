import chromadb
from sentence_transformers import SentenceTransformer
from gemini_utils import sensitive_data_log
from security_utils import encrypt_text
from supabase_utils import add_sensitive_value
import google.generativeai as genai

# Configure Gemini
import os
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Chroma setup
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="sensitive_chunks")

# Sentence embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")  # Or use InstructorEmbedding

# ✅ Embed and store a new sensitive phrase
def store_sensitive_phrase(phrase: str):
    embedding = model.encode(phrase).tolist()
    collection.add(
        documents=[phrase],
        embeddings=[embedding],
        ids=[phrase[:40]]  # ID must be unique; this is just a safe version
    )

# ✅ Check if a new phrase looks sensitive based on retrieval + Gemini
def is_phrase_sensitive(phrase: str) -> bool:
    embedding = model.encode(phrase).tolist()
    results = collection.query(query_embeddings=[embedding], n_results=5)

    # Build prompt using top similar examples
    context = "\n".join(results["documents"][0])
    prompt = f """ You are a data privacy assistant. Based on these past sensitive examples:

{context}

Is the following sentence sensitive or personal and should it be masked?

Sentence: "{phrase}"

Reply only with "Yes" or "No". """

    response = genai.GenerativeModel("models/gemini-2.0").generate_content(prompt)
    answer = response.text.strip().lower()
    return answer.startswith("yes")

# ✅ Main function to process + store if sensitive
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
