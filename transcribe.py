import tkinter as tk
from tkinter import filedialog, scrolledtext
from threading import Thread

import os
from docx import Document
from openai import OpenAI
from datetime import datetime

client = OpenAI(
    api_key="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"
)

def split_transcript(transcription, max_length=7000):
    segments = []
    while len(transcription) > 0:
        segment = transcription[:max_length].rsplit(' ', 1)[0]
        segments.append(segment)
        transcription = transcription[len(segment):].lstrip()
    return segments

def summarize_segment(segment, summary_length=200):
    prompt = (
        "Please provide a concise summary of up to " + str(summary_length) + " words, "
        "including separate sections for summary, action items, and key points:\n\n"
        f"{segment}"
    )

    response = client.chat.completions.create(
        model="gpt-4",
        temperature=0.7,
        messages=[
            {
                "role": "system",
                "content": prompt
            }
        ]
    )
    
    summarized_content = response.choices[0].message.content
    print(summarized_content)
    return summarized_content

def process_and_summarize(segments):
    for segment in segments:
        # Process each segment (this part is up to your specific logic)
        pass

    final_request = "Summarize the key points, action items, and provide a final summary of the meeting based on the previous segments."
    final_summary = summarize_segment(final_request, summary_length=200)  # Adjust summary length as needed
    return final_summary

def save_as_docx(summary, filename, meeting_date):
    new_doc = Document()
    new_doc.add_paragraph("Meeting Minutes", style='Heading 1')
    new_doc.add_paragraph(meeting_date, style='Normal')
    new_doc.add_paragraph(summary, style='Normal')
    new_doc.add_paragraph()  # Line break

    if os.path.exists(filename):
        old_doc = Document(filename)
        for element in old_doc.element.body:
            new_doc.element.body.append(element)

    new_doc.save(filename)

class TranscriptionApp(tk.Tk):
    def __init__(self, voice_recorder):
        super().__init__()
        self.voice_recorder = voice_recorder
        self.initialize_ui()
        self.transcription = ""

    def initialize_ui(self):
        self.title("Transcription Application")
        self.geometry("750x500")

        self.start_recording_button = tk.Button(self, text="Start Recording", command=self.toggle_recording)
        self.start_recording_button.pack(pady=5)

        self.transcription_display = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=10)
        self.transcription_display.pack(pady=10)
        self.transcription_display.config(state='disabled')

        self.initialize_additional_buttons()

    def initialize_additional_buttons(self):
        self.select_file_button = tk.Button(self, text="Select Audio File", command=self.load_audio_file)
        self.select_file_button.pack(pady=5)

        self.upload_transcript_button = tk.Button(self, text="Upload Transcript", command=self.load_transcript)
        self.upload_transcript_button.pack(pady=5)

        self.generate_transcript_button = tk.Button(self, text="Generate Transcript", command=self.create_transcript)
        self.generate_transcript_button.pack(pady=5)

        self.generate_minutes_button = tk.Button(self, text="Generate Minutes", command=self.create_minutes)
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
        transcription = self.voice_recorder.save_audio_and_transcribe()
        self.update_transcription_display(transcription)

    def update_transcription_display(self, transcription):
        self.transcription_display.config(state='normal')
        self.transcription_display.delete(1.0, tk.END)
        self.transcription_display.insert(tk.INSERT, transcription)
        self.transcription_display.config(state='disabled')

    def load_audio_file(self):
        filepath = filedialog.askopenfilename(title="Select Audio File", filetypes=[("MP3 Files", "*.mp3"), ("WAV Files", "*.wav")])

        if filepath:
            self.voice_recorder.mp3_file_name = filepath  # Assuming VoiceRecorder can handle external file paths
            transcription = self.voice_recorder._transcribe_audio()  # Call the transcription method
            self.update_transcription_display(transcription)

    def load_transcript(self):
        filepath = filedialog.askopenfilename(title="Select Transcript File", filetypes=[("Text Files", "*.txt")])
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as file:
                transcript = file.read()
                self.voice_recorder.transcription = transcript
            self.update_transcription_display(transcript)

    def create_transcript(self):
        if self.voice_recorder.mp3_file_name:
            transcription = self.voice_recorder._transcribe_audio()
            self.update_transcription_display(transcription)
        else:
            # Handle case where no audio file is loaded
            self.update_transcription_display("No audio file loaded for transcription.")

    def create_minutes(self):
        now = datetime.now()
        formatted_date = now.strftime("%B %d, %Y")
        transcription = self.voice_recorder.get_transcription()
        segments = split_transcript(transcription)
        summary = process_and_summarize(segments)
        doc_name = 'minutes_' + now.strftime("%B_%d_%Y") + '.docx'
        save_as_docx(summary, doc_name, formatted_date)
    
