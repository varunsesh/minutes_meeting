import logging
import os, sys
from threading import Thread
from openai import OpenAI
from datetime import datetime
from openai import OpenAI
from src.google_api_manager import GoogleAPIManager
import whisper

class CreateTranscription():
    def __init__(self, update_ui_callback=None):
        self.client = self.initialize_openai_client()
        self.transcription = ""
        self.mp3_file_name = ""
        self.model = None
        model_loading_thread = Thread(target=self.load_model, daemon=True)
        model_loading_thread.start()
        self.update_ui_callback = update_ui_callback

    def initialize_openai_client(self):
        return OpenAI()
    
    def load_model(self):
        """
        load the model on a seperate Thread .
        """
        self.model = whisper.load_model("medium")
        # Model loading logic
        print("Model is loading...")


    def create_transcript(self):
        """
        This function is used to transcribe an audio file into text. If an audio file is not loaded, the function will display an error message. If an audio file is loaded, the function will use the VoiceRecorder class to transcribe the audio file and display the transcription in the transcription display.
        """
        logging.info(f"Creating transcript of {self.mp3_file_name}")
        if self.mp3_file_name:
            transcription_result = self.model.transcribe(self.mp3_file_name)
            self.transcription = transcription_result["text"]
            self.update_ui_callback(self.transcription)
        else:
            # Handle case where no audio file is loaded
            self.update_ui_callback("No audio file loaded for transcription.")

    def split_transcript(self, max_length=7000):
        """
        Splits the transcript into segments of a given maximum length.

        Args:  max_length (int, optional): The maximum length of each segment. Defaults to 7000.

        Returns:
            list: A list of segments.
        """
        segments = []
        transcription = self.transcription
        if len(transcription) > (max_length + 500):
            while len(transcription) > 0:
                segment = transcription[:max_length].rsplit(' ', 1)[0]
                segments.append(segment)
                transcription = transcription[len(segment):].lstrip()
        else:
            segments.append(transcription)
        
        return segments

    def gpt_request(self, segment, is_final_segment):
        """
        This function is used to generate a summary for the GPT-4 model.

        Args:
            segment (str): The segment of the transcript to use as input for the prompt.
            is_final_segment (bool): A boolean indicating whether the given segment is the final segment of the transcript.

        Returns:
            str: The generated summary from the GPT-4 model.
        """
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
        """
        This function is used to generate summaries for the given segments of the transcript.

        Args:
            segments (list): A list of segments as prompts"""
        return [self.gpt_request(segment, i == len(segments) - 1) for i, segment in enumerate(segments)]


    def create_summary_audio(self, summary):
            
        meeting_summary = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.dirname(__file__)),  "..", "meeting_summary.mp3")

        response = self.client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=f"{summary}.Alright, it's time for me to switch gears from talk mode to stalk mode. I'm now entering record mode to capture today's discussion!"
        )
        response.stream_to_file(meeting_summary)

    def create_minutes(self):
        """
        This function is used to generate minutes for a meeting based on the recorded audio and transcript.

        The following steps are performed:

        1. The recorded audio is transcribed using the OpenAI API.
        2. The transcript is split into segments of a maximum length of 7000 characters.
        3. For each segment, a summary is generated using the GPT-4 model.
        4. The summaries are combined into a single document.
        5. The document is uploaded to Google Drive using the Google API.
        6. An audio summary of the meeting is generated using the OpenAI API and uploaded to Google Drive.

        """
        now = datetime.now()
        gsm = GoogleAPIManager()
        formatted_date = now.strftime("%B %d, %Y")
        doc_name = 'minutes_' + now.strftime("%B_%d_%Y") + '.docx'
        segments = self.split_transcript()
        summary = self.process_and_summarize(segments)
        gsm.update_docx_on_drive(summary, doc_name, formatted_date)
        self.create_summary_audio(summary)

    