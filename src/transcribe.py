from threading import Thread
import os
from openai import OpenAI
from datetime import datetime
from openai import OpenAI 
from dotenv import load_dotenv
from google_docs_manager import GoogleDocsManager
from PyQt5.QtWidgets import QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog

options = QFileDialog.Options()
options |= QFileDialog.DontUseNativeDialog

class TranscriptionApp(QMainWindow):
    def __init__(self, voice_recorder):
        super().__init__()
        self.voice_recorder = voice_recorder
        self.google_docs_manager = GoogleDocsManager()
        self.client = self.initialize_openai_client()
        self.initUI()

    def initialize_openai_client(self):
        load_dotenv()
        return OpenAI()
    
    def initUI(self):

        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)

        mainLayout = QVBoxLayout(centralWidget)
        buttonLayout = QHBoxLayout()

        self.transcription_display = QTextEdit(self)
        self.transcription_display.setReadOnly(True)
        mainLayout.addWidget(self.transcription_display)

        self.recap_button = QPushButton("Recap Previous Discussion", self)
        self.recap_button.clicked.connect(self.handle_recap)
        self.recap_button.setFixedSize(200, 40)
        buttonLayout.addWidget(self.recap_button)

        self.start_recording_button = QPushButton("Start Recording", self)
        self.start_recording_button.clicked.connect(self.toggle_recording)
        self.start_recording_button.setFixedSize(200, 40)
        buttonLayout.addWidget(self.start_recording_button)

        self.upload_recording_button = QPushButton("Upload Recording", self)
        self.upload_recording_button.clicked.connect(self.load_audio_file)
        self.upload_recording_button.setFixedSize(200, 40)
        buttonLayout.addWidget(self.upload_recording_button)

        self.upload_transcript_button = QPushButton("Upload Transcript", self)
        self.upload_transcript_button.clicked.connect(self.load_transcript)
        self.upload_transcript_button.setFixedSize(200, 40)
        buttonLayout.addWidget(self.upload_transcript_button)

        self.transcribe_button = QPushButton("Transcribe", self)
        self.transcribe_button.clicked.connect(self.create_transcript)
        self.transcribe_button.setFixedSize(200, 40)
        buttonLayout.addWidget(self.transcribe_button)

        self.summarize_button = QPushButton("Summarize", self)
        self.summarize_button.clicked.connect(self.create_minutes)
        self.summarize_button.setFixedSize(200, 40)
        buttonLayout.addWidget(self.summarize_button)

        mainLayout.addLayout(buttonLayout)
        


    def toggle_recording(self):
        if self.voice_recorder.is_active:
            self.end_recording()
            self.start_recording_button.setText("Start Recording")
        else:
            self.begin_recording()
            self.start_recording_button.setText("Stop Recording")

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

    def handle_recap(self):
        if getattr(self.voice_recorder.channel, 'get_busy', lambda: False)():
            self.voice_recorder.handle_recap("stop")
            self.recap_button.setText("Recap Previous Discussion")
        else:
            self.voice_recorder.handle_recap("play")
            self.recap_button.setText("Stop")
    
    def update_transcription_display(self, transcription):
        self.transcription_display.clear()
        self.transcription_display.setText(transcription)

    def load_audio_file(self):
        file_name,_ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.mp3 *.wav)", options=options)
        if file_name:
            self.voice_recorder.mp3_file_name = file_name  # Assuming VoiceRecorder can handle external file paths
            self.voice_recorder.transcription = self.voice_recorder._transcribe_audio()
            self.update_transcription_display(self.voice_recorder.transcription)

    def load_transcript(self):
        file_name,_ = QFileDialog.getOpenFileName(self, "Select Transcript File", "","Text Files (*.txt)", options=options)
        if file_name:
            with open(file_name, 'r', encoding='utf-8') as file:
                transcript = file.read()
                self.voice_recorder.transcription = transcript
            self.update_transcription_display(transcript)

    def create_transcript(self):
        print(self.voice_recorder.mp3_file_name)
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

        segments = self.split_transcript()
        summary = self.process_and_summarize(segments)
        self.google_docs_manager.save_and_update_docx_on_drive(summary, doc_name, formatted_date, google_doc_id)
        self.create_summary_audio(summary)

    