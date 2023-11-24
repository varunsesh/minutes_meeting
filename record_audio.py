import pyaudio
import wave
from pydub import AudioSegment
import whisper
from threading import Thread
import tkinter as tk
from tkinter import scrolledtext, ttk
from datetime import datetime
import os

class AudioRecorder:
    def __init__(self):
        self.device_index = None
        self.is_recording = False
        self.frames = []
        self.p = None
        self.stream = None
        self.model = whisper.load_model("small")

    def set_device_index(self, device_name):
        self.p = pyaudio.PyAudio()
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            if device_name in dev['name']:
                self.device_index = i
                return
        self.device_index = None
        print(f"Device '{device_name}' not found.")

    def start_recording(self):
        self.is_recording = True
        self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024, input_device_index=self.device_index)
        self.frames = []

    def stop_recording(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

    def record_audio(self):
        while self.is_recording:
            data = self.stream.read(1024, exception_on_overflow=False)
            self.frames.append(data)

    def save_and_transcribe(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        wav_filename = f"recording_{timestamp}.wav"
        mp3_filename = f"recording_{timestamp}.mp3"
        transcription_file = f"transcription_{timestamp}.txt"

        with wave.open(wav_filename, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(b''.join(self.frames))

        audio_segment = AudioSegment.from_wav(wav_filename)
        audio_segment.export(mp3_filename, format="mp3")
        os.remove(wav_filename)

        result = self.model.transcribe(mp3_filename)
        os.remove(mp3_filename)

        # with open(transcription_file, "w") as f:
        #     f.write(result["text"])

        return result["text"]

class RecordingApp(tk.Tk):
    def __init__(self, recorder):
       super().__init__()
       self.recorder = recorder
       self.title("Audio Recorder")
       self.geometry("400x400")
       self.recording_state = False  # Added to track the recording stat
       self.device_label = tk.Label(self, text="Select Input Device:")
       self.device_label.pack(pady=5)
       self.device_combobox = ttk.Combobox(self, values=["Stereo Mix", "Microphone"])
       self.device_combobox.pack(pady=5)
       self.device_combobox.set("Stereo Mix")
       self.toggle_button = tk.Button(self, text="Start Recording", command=self.toggle_recording)
       self.toggle_button.pack(pady=10) 
       self.transcription_text = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=10)
       self.transcription_text.pack(pady=10)
       self.transcription_text.config(state='disabled')
       self.__transcription = ""
       
    def toggle_recording(self):
        if self.recording_state:
            self.stop_recording()
            self.toggle_button.config(text="Start Recording")
        else:
            self.start_recording()
            self.toggle_button.config(text="Stop Recording")
        self.recording_state = not self.recording_state


    def start_recording(self):
        selected_device = self.device_combobox.get()
        self.recorder.set_device_index(selected_device)
        self.recorder.start_recording()
        self.recording_thread = Thread(target=self.recorder.record_audio)
        self.recording_thread.start()

    def stop_recording(self):
        self.recorder.stop_recording()
        self.recording_thread.join()
        self.__transcription += self.recorder.save_and_transcribe()
        self.transcription_text.config(state='normal')
        self.transcription_text.delete(1.0, tk.END)
        self.transcription_text.insert(tk.INSERT, self.__transcription)
        self.transcription_text.config(state='disabled')

    def get_transcript(self):
        return self.__transcription

if __name__ == "__main__":
    recorder = AudioRecorder()
    app = RecordingApp(recorder)
    app.mainloop()
