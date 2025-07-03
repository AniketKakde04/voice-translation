from gtts import gTTS

def text_to_speech(text: str, output_path: str = "static/output.mp3") -> str:
    tts = gTTS(text, lang='en')
    tts.save(output_path)
    return output_path
