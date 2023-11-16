import pyaudio
import wave
from pydub import AudioSegment
import openai
from dotenv import load_dotenv
import os

def transcribe_audio(client):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)

    frames = []

    try:
        print("Recording... (Press Ctrl+C to stop)")
        while True:
            data = stream.read(1024)
            frames.append(data)

    except KeyboardInterrupt:
        print("\nRecording stopped")

    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

        temp_wav_filename = "temp_audio.wav"
        with wave.open(temp_wav_filename, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(b"".join(frames))

        audio_segment = AudioSegment.from_wav(temp_wav_filename)
        temp_mp3_filename = "temp_audio.mp3"
        audio_segment.export(temp_mp3_filename, format="mp3")

        with open(temp_mp3_filename, "rb") as mp3_file:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=mp3_file)
        
        print("Transcription:", transcript.text)
        os.remove(temp_wav_filename)
        os.remove(temp_mp3_filename)
    return transcript.text

if __name__ == "__main__":
    load_dotenv()
    client = openai.Client()
    transcribe_audio(client)
