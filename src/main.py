from transcribe import TranscriptionApp 
from voice_recorder import VoiceRecorder
from audio_utils import audio_setup


if __name__ == "__main__":
    print("Starting the recorder app...")
    try :
        audio_setup()
        recorder = VoiceRecorder() 
        app = TranscriptionApp(recorder) 
        app.mainloop()
    except Exception as e :
        print("Exception Failed to initialize application", e)

    
