from faster_whisper import WhisperModel

model = WhisperModel("base")

def transcribe_audio(file_path):

    segments, info = model.transcribe(file_path)

    text = ""

    for segment in segments:
        text += segment.text

    return text.strip()