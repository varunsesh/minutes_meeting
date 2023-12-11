from transcribe import TranscriptionApp 
from voice_recorder import VoiceRecorder
from audio_utils import audio_setup
import sys
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    print("Starting the recorder app...")
    try :
        audio_setup()
        recorder = VoiceRecorder() 
        app = QApplication(sys.argv)
        main_window = TranscriptionApp(recorder)
        main_window.show()
        sys.exit(app.exec_())
    except Exception as e :
        print("Exception Failed to initialize application", e)

    
