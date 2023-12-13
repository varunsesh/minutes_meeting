from transcribe import TranscriptionApp 
from voice_recorder import VoiceRecorder
from audio_utils import audio_setup
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

if __name__ == "__main__":
    print("Starting the recorder app...")
    try :
        app = QApplication(sys.argv)
        audio_setup()
        recorder = VoiceRecorder() 
        main_window = TranscriptionApp(recorder)
        main_window.setWindowTitle('Mr Minutes')
        main_window.setGeometry(100, 100, 800, 600)
        main_window.setWindowIcon(QIcon('app_icon.ico'))
        main_window.show()
        sys.exit(app.exec_())
    except Exception as e :
        print("Exception Failed to initialize application", e)

    
