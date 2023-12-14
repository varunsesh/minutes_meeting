from src import transcribe , voice_recorder, audio_utils
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from dotenv import load_dotenv

def main():
    """
    This function initializes the main window of the application.
    """
    print("Starting the recorder app...")
    try :
        load_dotenv()
        app = QApplication(sys.argv)
        audio_utils.audio_setup()
        recorder = voice_recorder.VoiceRecorder() 
        main_window = transcribe.TranscriptionApp(recorder)
        main_window.setWindowTitle('Mr Minutes')
        main_window.setGeometry(100, 100, 800, 600)
        main_window.setWindowIcon(QIcon('assets/app_icon.ico'))
        main_window.show()
        sys.exit(app.exec_())
    except Exception as e :
        print("Exception Failed to initialize application", e)

    
if __name__ == "__main__":
    main()