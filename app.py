import os
from flask import Flask, request
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
from gemini_utils import transcribe_and_translate
from twilio_utils import download_audio_file
from tts_utils import text_to_speech

load_dotenv()

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    num_media = int(request.form.get("NumMedia", 0))
    resp = MessagingResponse()

    if num_media == 0:
        resp.message("Please send a voice message in any Indian language.")
        return str(resp)

    media_url = request.form.get("MediaUrl0")
    media_content_type = request.form.get("MediaContentType0", "")

    if not any(fmt in media_content_type for fmt in ["audio", "mp3", "wav", "ogg"]):
        resp.message("Unsupported audio format. Please send MP3, WAV or OGG voice note.")
        return str(resp)

    try:
        audio_data = download_audio_file(media_url)
        translated_text = transcribe_and_translate(audio_data)

        # Convert to speech
        output_path = text_to_speech(translated_text)
        voice_url = request.url_root + "static/output.mp3"

        # WhatsApp voice reply
        msg = resp.message("🔊 Here's your translated voice note.")
        msg.media(voice_url)

    except Exception as e:
        print("Error:", e)
        resp.message("Sorry, could not process your voice note. Try again.")

    return str(resp)
