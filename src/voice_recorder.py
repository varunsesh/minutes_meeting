import logging
import sys
import pyaudio
import wave
from pydub import AudioSegment
from datetime import datetime
from threading import Thread
import os
import pygame


pygame.mixer.init()
class VoiceRecorder:
    """
    The VoiceRecorder class provides an interface for recording and transcribing audio.
    """
    def __init__(self):
        self.is_active = False
        self.audio_frames = []
        self.pyaudio_instance = pyaudio.PyAudio()
        self.channel = pygame.mixer.find_channel(True)
        self.recording_thread = None
        self.audio_stream = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def begin_recording(self):
        """Starts recording audio using PyAudio."""
        self.is_active = True
        self.audio_stream = self.pyaudio_instance.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
        self.audio_frames = []
        self.recording_thread = Thread(target=self.capture_audio, daemon=True)
        self.recording_thread.start()
    
    def capture_audio(self):
        """
        This function is used to capture audio data from the microphone. It uses the PyAudio library to access the audio stream and stores the data in a list. The function continuously reads data from the stream and appends it to the list until the recording is stopped.

        Parameters:
        self (object): The instance of the VoiceRecorder class.

        Returns:
        None

        Raises:
        IOError: If there is an error reading from the audio stream.
        """
        while self.is_active:
            try:
                data = self.audio_stream.read(1024, exception_on_overflow=False)
                if not self.channel.get_busy():
                    self.audio_frames.append(data)
            except IOError as e:
                # Handle the error as needed
                self.logger.error(f"I/O error:{e}")

    def end_recording(self):
        """Stops the recording process and closes the audio stream."""
        self.is_active = False
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
        if self.recording_thread.is_alive():
            self.recording_thread.join()
        
        audio_path = self._save_audio()
        return audio_path

    def _save_audio(self):
        """
        Saves the recorded audio to a WAV file and an MP3 file.

        The WAV file is stored in the Recordings folder, and the MP3 file is stored in the same folder with a different file name. The function uses the PyAudio and wave libraries to access the audio stream and save the data to the WAV file. The AudioSegment library is used to convert the WAV file to an MP3 file.

        Parameters:
        self (object): The instance of the VoiceRecorder class.

        Raises:
        IOError: If there is an error reading from or writing to the audio stream.
        """
        
        recordings_folder = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__),  "..", "recordings")
        os.makedirs(recordings_folder, exist_ok=True)

        # Format file names with the path to the 'Recordings' folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        wav_file_path = os.path.join(recordings_folder, f"recording_{timestamp}.wav")
        mp3_file_path = os.path.join(recordings_folder, f"recording_{timestamp}.mp3")

        with wave.open(wav_file_path, "wb") as wave_file:
            wave_file.setnchannels(1)
            wave_file.setsampwidth(self.pyaudio_instance.get_sample_size(pyaudio.paInt16))
            wave_file.setframerate(16000)
            wave_file.writeframes(b''.join(self.audio_frames))

        audio_segment = AudioSegment.from_wav(wav_file_path)
        audio_segment.export(mp3_file_path, format="mp3")
        os.remove(wav_file_path)
        return mp3_file_path
    
    def handle_recap(self, action):
        """
        This function is used to play the meeting summary audio. It checks if the file exists, and if it does, it plays the audio using Pygame. If the audio is already playing, the function prints a message to the console. If the file does not exist, the function prints an error message to the console.

        Parameters:
        self (object): The instance of the VoiceRecorder class.
        action (str): The action to be performed on the audio. Can be "play" or "stop".
        
        Raises:
        IOError: If there is an error playing the audio.
        """
        try:
            sound_file = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.dirname(__file__)),  "..", "meeting_summary.mp3")
            if not os.path.exists(sound_file):
                self.logger.info(f"File '{sound_file}' not found.")
                return
            if action == "play":
                if not self.channel.get_busy():
                    self.channel.play(pygame.mixer.Sound(sound_file))
                else:
                    self.logger.info("Audio is already playing.")
            elif action == "stop":
                self.channel.stop()  # Stopping a channel that isn't playing is safe
            else:
                self.logger.error(f"Unknown action: {action}")
                
        except Exception as e:
            self.logger.error(f"Audio summary does not exist.{e}")

    def __del__(self):
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
