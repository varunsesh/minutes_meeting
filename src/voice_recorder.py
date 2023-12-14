import sys
import pyaudio
import wave
from pydub import AudioSegment
from datetime import datetime
import os
import pygame
import whisper

pygame.mixer.init()
class VoiceRecorder:
    def __init__(self):
        self.is_active = False
        self.audio_frames = []
        self.pyaudio_instance = pyaudio.PyAudio()
        self.channel = pygame.mixer.find_channel(True)
        self.audio_stream = None
        self.mp3_file_name = ""
        self.transcription = ""
        self.transcription_model = whisper.load_model("medium")

    def begin_recording(self):
        self.is_active = True
        self.audio_stream = self.pyaudio_instance.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
        self.audio_frames = []
    
    def capture_audio(self):
        while self.is_active:
            try:
                data = self.audio_stream.read(1024, exception_on_overflow=False)
                if not self.channel.get_busy():
                    self.audio_frames.append(data)
            except IOError as e:
                # Handle the error as needed
                print("I/O error:", e)

    def end_recording(self):
        self.is_active = False
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None

    def save_audio_and_transcribe(self):
        self._save_audio()
        return self._transcribe_audio()

    def _save_audio(self):
        if getattr(sys, 'frozen', False):
            # The application is frozen (packaged)
            recordings_folder = os.path.join(os.path.dirname(sys.executable),  "..", "recordings")
        else:
            # The application is not frozen (running from source)
            recordings_folder = os.path.join(os.path.dirname(__file__), "..", "recordings")
        os.makedirs(recordings_folder, exist_ok=True)

        # Format file names with the path to the 'Recordings' folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        wav_file_path = os.path.join(recordings_folder, f"recording_{timestamp}.wav")
        mp3_file_path = os.path.join(recordings_folder, f"recording_{timestamp}.mp3")
        self.mp3_file_name = mp3_file_path

        with wave.open(wav_file_path, "wb") as wave_file:
            wave_file.setnchannels(1)
            wave_file.setsampwidth(self.pyaudio_instance.get_sample_size(pyaudio.paInt16))
            wave_file.setframerate(16000)
            wave_file.writeframes(b''.join(self.audio_frames))

        audio_segment = AudioSegment.from_wav(wav_file_path)
        audio_segment.export(self.mp3_file_name, format="mp3")
        os.remove(wav_file_path)

    def _transcribe_audio(self):
        transcription_result = self.transcription_model.transcribe(self.mp3_file_name)
        self.transcription = transcription_result["text"]
        return self.transcription
    
    def handle_recap(self, action):
        try:
            sound_file = "src/meeting_summary.mp3"
            if not os.path.exists(sound_file):
                print(f"File '{sound_file}' not found.")
                return
            if action == "play":
                if not self.channel.get_busy():
                    self.channel.play(pygame.mixer.Sound(sound_file))
                else:
                    print("Audio is already playing.")
            elif action == "stop":
                self.channel.stop()  # Stopping a channel that isn't playing is safe
            else:
                print(f"Unknown action: {action}")
                
        except Exception as e:
            print("Audio summary does not exist.",e)

    def __del__(self):
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
