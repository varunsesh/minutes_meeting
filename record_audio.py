import pyaudio
import wave
from pydub import AudioSegment
import whisper
from threading import Thread
import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog
from datetime import datetime
import os
import time
import sys

class AudioRecorder:
    def __init__(self):
        self.device_index = None
        self.is_recording = False
        self.frames = []
        self.p = None
        self.stream = None
        self._mp3filename = ""
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
        print("Stopping in parent class")
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            print("Swooping down")
            self.stream = None
        # Don't terminate self.p here

    def record_audio(self):
        while self.is_recording:
            data = self.stream.read(1024, exception_on_overflow=False)
            self.frames.append(data)

    def transcribe(self):
        result = self.model.transcribe(self._mp3filename)
        return result["text"]

    def save_for_transcribe(self):
        print("Saving for transcription...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        wav_filename = f"recording_{timestamp}.wav"
        self._mp3filename = f"recording_{timestamp}.mp3"

        try:
            with wave.open(wav_filename, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
                wf.setframerate(16000)
                wf.writeframes(b''.join(self.frames))
        finally:
            if self.p:
                self.p.terminate()
                self.p = None

        audio_segment = AudioSegment.from_wav(wav_filename)
        audio_segment.export(self._mp3filename, format="mp3")
        os.remove(wav_filename)

    
    def transcribe_from_recorded_audio(self, mp3filename):
        result = self.model.transcribe(mp3filename)
        return result["text"]

class RecordingApp(tk.Tk):
    def __init__(self, recorder):
       super().__init__()
       self.__generate_minutes = False
       self.recorder = recorder
       self.title("Audio Recorder")
       self.geometry("750x500")
       self.recording_state = False  # Added to track the recording stat
       self.device_label = tk.Label(self, text="Select Input Device:")
       self.device_label.pack(pady=5)
       self.device_combobox = ttk.Combobox(self, values=["Stereo Mix", "Microphone"])
       self.device_combobox.pack(pady=5)
       self.device_combobox.set("Stereo Mix")
       self.toggle_button = tk.Button(self, text="Start Recording", command=self.toggle_recording)
       self.toggle_button.pack(pady=5)
       self.__transcription = ""
       self.select_file_button = tk.Button(self, text="Select Audio File", command=self.select_file)
       self.select_file_button.pack(pady=5)
       self.upload_transcript_button = tk.Button(self, text="Upload Transcript File", command=self.upload_transcript)
       self.upload_transcript_button.pack(pady=5)
       self.generate_transcript_button = tk.Button(self, text="Generate Transcript File", command=self.generate_transcript_now)
       self.generate_transcript_button.pack(pady=5)
       self.generate_minutes_button = tk.Button(self, text="Generate Minutes File", command=self.generate_minutes)
       self.generate_minutes_button.pack(pady=5)
       self.transcription_text = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=10)
       self.transcription_text.pack(pady=10)
       self.transcription_text.config(state='disabled')

       # Configure the columns and rows to expand with the window
       self.grid_columnconfigure(0, weight=1)  # Make column 0 expandable
       self.grid_columnconfigure(1, weight=1)  # Make column 1 expandable
       self.grid_rowconfigure(0, weight=1)     # Make row 0 expandable

    def start_transcription(self):
        self.progress_bar.start(10)  # Start the indeterminate progress bar
        Thread(target=self.run_transcription, daemon=True).start()

    def run_transcription(self):
        # Simulate transcription process
        time.sleep(5)  # Replace with actual transcription call
        self.stop_transcription()

    def stop_transcription(self):
        self.progress_bar.stop()  # Stop the progress bar
        # Update the GUI with transcription results
        # ...

    def toggle_recording(self):
        if self.recording_state:
            self.stop_recording()
            self.toggle_button.config(text="Start Recording")
        else:
            self.start_recording()
            self.toggle_button.config(text="Stop Recording")
            #self.start_transcription()
        self.recording_state = not self.recording_state


    def start_recording(self):
        print("start recording...")
        selected_device = self.device_combobox.get()
        self.recorder.set_device_index(selected_device)
        self.recorder.start_recording()
        self.recording_thread = Thread(target=self.recorder.record_audio)
        self.recording_thread.start()

    def stop_recording(self):
        try:
            print("stopping recording...")
            self.recorder.stop_recording()
            if self.recording_thread.is_alive():
                self.recording_thread.join()
            self.recorder.save_for_transcribe()
        except Exception as e:
            print(f"Error occurred: {e}")
            raise
        

    def get_transcript(self):
        return self.__transcription
    
    def select_file(self):
        filepath = filedialog.askopenfilename(title="Select Audio File", filetypes=[("Audio Files", "*.mp3 *.wav")])
        if filepath:
            self.__transcription = self.recorder.transcribe_from_recorded_audio(filepath)
            self.transcription_text.config(state='normal')
            self.transcription_text.delete(1.0, tk.END)
            self.transcription_text.insert(tk.INSERT, self.__transcription)
            self.transcription_text.config(state='disabled')

    def upload_transcript(self):
        filepath = filedialog.askopenfilename(title="Select Transcript File", filetypes=[("Text Files", "*.txt")])
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as file:
                transcript = file.read()
            self.__transcription = transcript
            self.transcription_text.config(state='normal')
            self.transcription_text.delete(1.0, tk.END)
            self.transcription_text.insert(tk.INSERT, self.__transcription)
            self.transcription_text.config(state='disabled')
    
    def generate_transcript_now(self):
        self.__transcription += self.recorder.transcribe()
        self.transcription_text.config(state='normal')
        self.transcription_text.delete(1.0, tk.END)
        self.transcription_text.insert(tk.INSERT, self.__transcription)
        self.transcription_text.config(state='disabled')
        
    def generate_minutes(self):
        self.__generate_minutes = True

    def get_permission(self):
        return self.__generate_minutes

if __name__ == "__main__":
    print("Starting the recorder app...")
    recorder = AudioRecorder()
    app = RecordingApp(recorder)
    app.mainloop()