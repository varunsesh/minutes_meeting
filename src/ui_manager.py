from PyQt5.QtWidgets import QMainWindow, QTextEdit, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout
from PyQt5.QtGui import QIcon
from src import voice_recorder as vr , transcribe as tr

options = QFileDialog.Options()
options |= QFileDialog.DontUseNativeDialog

class UIManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.voice_recorder = vr.VoiceRecorder()
        self.transcribe = tr.CreateTranscription(self.update_transcription_display)
        self.initUI()

    def initUI(self):
        """
        Initialize the main window with the given voice recorder.

        Args:
            voice_recorder (VoiceRecorder): The voice recorder to use for recording and transcribing audio.
        """

        self.setWindowTitle('Mr Minutes')
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon('assets/app_icon.ico'))
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
        self.transcribe_button.clicked.connect(self.transcribe.create_transcript)
        self.transcribe_button.setFixedSize(200, 40)
        buttonLayout.addWidget(self.transcribe_button)

        self.summarize_button = QPushButton("Summarize", self)
        self.summarize_button.clicked.connect(self.transcribe.create_minutes)
        self.summarize_button.setFixedSize(200, 40)
        buttonLayout.addWidget(self.summarize_button)

        mainLayout.addLayout(buttonLayout)

    def toggle_recording(self):
        """
        This function is used to start and stop recording audio.
        """
        if self.voice_recorder.is_active:
            audio_file = self.voice_recorder.end_recording()
            self.transcribe.mp3_file_name = audio_file
            self.transcribe.create_transcript()
            self.start_recording_button.setText("Start Recording")
        else:
            self.voice_recorder.begin_recording()
            self.start_recording_button.setText("Stop Recording")

    def handle_recap(self):
        """This function is used to recap the previous discussion. If the previous discussion is still in progress, it will be stopped. If there is no previous discussion, this function will do nothing."""
        if getattr(self.voice_recorder.channel, 'get_busy', lambda: False)():
            self.voice_recorder.handle_recap("stop")
            self.recap_button.setText("Recap Previous Discussion")
        else:
            self.voice_recorder.handle_recap("play")
            self.recap_button.setText("Stop")

    def update_transcription_display(self, transcription):
        """
        This function is used to update the transcription display with the given transcription.

        Args:
            transcription (str): The transcription to display in the transcription display.
        """
        self.transcription_display.clear()
        self.transcription_display.setText(transcription)
    
    def load_audio_file(self):
        """
        Opens a file dialog to allow the user to select an audio file. If a file is selected, the 
        `VoiceRecorder.mp3_file_name` attribute is set to the file path. The transcription of the audio 
        file is then generated using the `VoiceRecorder. transcribe_audio()` method. The transcribed 
        text is displayed in the transcription display.
        """
        file_name,_ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.mp3 *.wav)", options=options)
        if file_name:
            self.transcribe.mp3_file_name = file_name  # Assuming VoiceRecorder can handle external file paths
            self.transcribe.transcription = self.transcribe.transcribe_audio()
            self.update_transcription_display(self.transcribe.transcription)

    def load_transcript(self):
        """
        This function is used to load a transcript file into the application.
        """
        file_name,_ = QFileDialog.getOpenFileName(self, "Select Transcript File", "","Text Files (*.txt)", options=options)
        if file_name:
            self.transcribe.mp3_file_name = ""
            with open(file_name, 'r', encoding='utf-8') as file:
                transcript = file.read()
                self.transcribe.transcription = transcript
            self.update_transcription_display(transcript)