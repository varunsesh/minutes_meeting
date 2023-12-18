import logging
import os, sys, json
from datetime import datetime
from openai import OpenAI
from src.google_api_manager import GoogleAPIManager
from whisper import Whisper

class TranscriptionManager():
    def __init__(self, whisper_model: Whisper, update_ui_callback):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = self.init_openai_client()
        self.transcription = ""
        self.mp3_file_name = ""
        self.whisper_model = whisper_model
        self.update_ui_callback = update_ui_callback
        self.conversation_history = []
    
    def init_openai_client(self):
        hasKey = os.environ.get("OPENAI_API_KEY")
        if not hasKey:
            self.logger.error("Missing OpenAI API Key")
            return
        return OpenAI()
            


    def create_transcript(self):
        """
        This function is used to transcribe an audio file into text. If an audio file is not loaded, the function will display an error message. If an audio file is loaded, the function will use the VoiceRecorder class to transcribe the audio file and display the transcription in the transcription display.
        """
        self.logger.info(f"Creating transcript of {self.mp3_file_name}")
        if not self.mp3_file_name:
            self.logger.error("No audio file loaded for transcription.")
            self.update_ui_callback("No audio file loaded for transcription.")
            return

        transcription_result = self.whisper_model.transcribe(self.mp3_file_name)
        self.transcription = transcription_result["text"]
        self.update_ui_callback(self.transcription)

    def split_transcript(self, max_length=16000):
        """
        Splits the transcript into segments of a given maximum length.

        Args:  max_length (int, optional): The maximum length of each segment. Defaults to 16000.

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
        elif len(transcription) > 0:
            segments.append(transcription)
        
        return segments

    def update_conversation_history(self, system_message, user_message):
        """
        Update the conversation history.
        """
        self.conversation_history.extend([
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ])
    
    def gpt_request(self, segment, is_final_segment):
        """
        Send a request to GPT-4 to process a segment of a meeting transcript.
        If it is the final segment, also request a summary with objective, key points, and action items.
        """
        instruction = "Carefully review the segment provided from a meeting transcript, ensuring you pay close attention to all details. Be aware of the total word count of the entire transcript. Upon receipt of this content, simply acknowledge its reception."

        # Process the segment
        segment_response = self.create_gpt_response(instruction, segment)
        self.logger.info(segment_response)
        
        if is_final_segment:
            summary_responses = self.get_meeting_summary()
            return summary_responses
        return None

    def create_gpt_response(self, system_message, user_message):
        """
        Create a response from GPT-4 based on the given instruction and user content.
        """
        self.update_conversation_history(system_message, user_message)
        
        response = self.client.chat.completions.create(
            model="gpt-4-1106-preview",
            temperature=0.7,
            messages=self.conversation_history
        )
        return response.choices[0].message.content

    def get_meeting_summary(self):
        """
        Get a summary of the meeting including objective, key points, and action items.
        """
        
        summary = self.create_gpt_response('Total combined word count of objective, key points and action items should be less than half of the word count of original transcript.'
                                           ' Ensure clarity and presentation quality in the sentence formation. The summary should be structured as follows: '
                                           '{"objective": "Brief paragraph on the meeting objective", "key_points": ["1. Key point..", "2. Key point 2", ...],"action_items": ["1. Action item", "2. Action item", ...]}' , 
                                           'Now Provide a summary of the meeting transcript')
        
        return summary

    def process_and_summarize(self, segments):
        """
        This function is used to generate summaries for the given segments of the transcript.

        Args:
            segments (list): A list of segments as prompts"""
        return [self.gpt_request(segment,  i == len(segments) - 1) for i, segment in enumerate(segments)]
        


    def create_summary_audio(self, summary):
            
        meeting_summary = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.dirname(__file__)),  "..", "meeting_summary.mp3")

        summary_text = f"{summary['objective']}. Key Points disscussed were {summary['key_points']}. Tasks that were pending {summary['action_items']}. Alright, it's time for me to switch gears from talk mode to stalk mode. I'm now entering record mode to capture today's discussion!"    
        
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=summary_text
        )
        response.stream_to_file(meeting_summary)

    def create_minutes(self):
        """Generate minutes for a meeting."""
        now = datetime.now()
        gsm = GoogleAPIManager()
        formatted_date = now.strftime("%B %d, %Y")
        doc_name = 'minutes_' + now.strftime("%B_%d_%Y") + '.docx'
        segments = self.split_transcript()
        summary = self.process_and_summarize(segments)[0]
        try:
            summary = json.loads(summary)
        except Exception as e:
            self.logger.error(f"Error {e}")
        # summary = "Update the Google Doc with the given summary, local file name, and date. param summary: The summary to add to the Google Doc (list of strings)"
        # "param local_fname: The local temp file name of the Word document :param date: The date to add to the Google Doc The updated Google Doc ID"
        if summary:
            self.conversation_history = []
            gsm.update_docx_on_drive(summary, doc_name, formatted_date)
            self.create_summary_audio(summary)

    