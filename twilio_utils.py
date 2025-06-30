import requests

def download_audio_file(audio_url: str) -> bytes:
    # Twilio sends media as temporary public URL
    response = requests.get(audio_url)
    response.raise_for_status()
    return response.content
