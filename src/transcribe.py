import tkinter as tk
from tkinter import filedialog, scrolledtext
from threading import Thread
from io import BytesIO
import os
from openai import OpenAI
from datetime import datetime
from openai import OpenAI 
from dotenv import load_dotenv
from google_docs_manager import GoogleDocsManager


class TranscriptionApp(tk.Tk):
    def __init__(self, voice_recorder):
        super().__init__()
        self.voice_recorder = voice_recorder
        self.google_docs_manager = GoogleDocsManager()
        self.client = self.initialize_openai_client()
        self.initialize_ui()

    def initialize_openai_client(self):
        load_dotenv()
        return OpenAI()

    def initialize_ui(self):
        self.title("Mr Minutes")
        self.geometry("750x500")
        self.start_recording_button = tk.Button(self, text="Start Recording", command=self.toggle_recording)
        self.start_recording_button.pack(pady=5)

        self.transcription_display = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=10)
        self.transcription_display.pack(pady=10)
        self.transcription_display.config(state='disabled')

        self.initialize_additional_buttons()

    def initialize_additional_buttons(self):
        self.select_file_button = tk.Button(self, text="Upload Recording", command=self.load_audio_file)
        self.select_file_button.pack(pady=5)

        self.upload_transcript_button = tk.Button(self, text="Upload Transcript", command=self.load_transcript)
        self.upload_transcript_button.pack(pady=5)

        self.generate_transcript_button = tk.Button(self, text="Transcribe", command=self.create_transcript)
        self.generate_transcript_button.pack(pady=5)

        self.generate_minutes_button = tk.Button(self, text="Summarize", command=self.create_minutes)
        self.generate_minutes_button.pack(pady=5)

    def toggle_recording(self):
        if self.voice_recorder.is_active:
            self.end_recording()
            self.start_recording_button.config(text="Start Recording")
        else:
            self.begin_recording()
            self.start_recording_button.config(text="Stop Recording")

    def begin_recording(self):
        self.voice_recorder.begin_recording()
        self.recording_thread = Thread(target=self.voice_recorder.capture_audio, daemon=True)
        self.recording_thread.start()

    def end_recording(self):
        self.voice_recorder.end_recording()
        if self.recording_thread.is_alive():
            self.recording_thread.join()
        self.voice_recorder.transcription = self.voice_recorder.save_audio_and_transcribe()
        self.update_transcription_display(self.voice_recorder.transcription)

    def update_transcription_display(self, transcription):
        self.transcription_display.config(state='normal')
        self.transcription_display.delete(1.0, tk.END)
        self.transcription_display.insert(tk.INSERT, transcription)
        self.transcription_display.config(state='disabled')

    def load_audio_file(self):
        filepath = filedialog.askopenfilename(title="Select Audio File", filetypes=[("MP3 Files", "*.mp3"), ("WAV Files", "*.wav")])

        if filepath:
            self.voice_recorder.mp3_file_name = filepath  # Assuming VoiceRecorder can handle external file paths
            self.voice_recorder.transcription = self.voice_recorder._transcribe_audio()  # Call the transcription method
            self.update_transcription_display(self.voice_recorder.transcription)

    def load_transcript(self):
        filepath = filedialog.askopenfilename(title="Select Transcript File", filetypes=[("Text Files", "*.txt")])
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as file:
                transcript = file.read()
                self.voice_recorder.transcription = transcript
            self.update_transcription_display(transcript)

    def create_transcript(self):
        if self.voice_recorder.mp3_file_name:
            self.voice_recorder.transcription = self.voice_recorder._transcribe_audio()
            self.update_transcription_display(self.voice_recorder.transcription)
        else:
            # Handle case where no audio file is loaded
            self.update_transcription_display("No audio file loaded for transcription.")

    def split_transcript(self, max_length=7000):
        segments = []
        transcription = self.voice_recorder.transcription
        if len(transcription) > (max_length + 500):
            while len(transcription) > 0:
                segment = transcription[:max_length].rsplit(' ', 1)[0]
                segments.append(segment)
                transcription = transcription[len(segment):].lstrip()
        else:
            segments.append(transcription)
        
        return segments

    def gpt_request(self, segment, is_final_segment):
        instruction = (
            "Please carefully read the following segment of a meeting transcript. Pay close attention to the details, as they will be important for a summary you'll be asked to provide later. However, do not start summarizing until you receive a specific request to do so"
        )
        prompt = f"{instruction}\n\n{segment}"
        if is_final_segment:
            prompt += "Now, provide the objective, key points and (action items or tasks) based on the entire transcript, ensuring the content does not exceed half the length of original content in terms of character count."
            response = self.client.chat.completions.create(
            model="gpt-4",
            temperature=0.7,
            messages=[{"role": "system", "content": prompt}]
        )
        return response.choices[0].message.content

    def process_and_summarize(self, segments):
        return [self.gpt_request(segment, i == len(segments) - 1) for i, segment in enumerate(segments)]


    def create_summary_audio(self, summary):
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=f"{summary}.Alright, it's time for me to switch gears from talk mode to stalk mode. I'm now entering record mode to capture today's discussion!"
        )
        response.stream_to_file("meeting_summary.mp3")

    def create_minutes(self):
        now = datetime.now()
        formatted_date = now.strftime("%B %d, %Y")
        doc_name = 'minutes_' + now.strftime("%B_%d_%Y") + '.docx'
        google_doc_id = os.environ.get("GOOGLE_DOC_ID")

        transcription = self.voice_recorder.get_transcription()
        segments = self.split_transcript()
        summary = self.process_and_summarize(segments)
        self.google_docs_manager.save_and_update_docx_on_drive(summary, doc_name, formatted_date, google_doc_id)
        self.create_summary_audio(summary)

    