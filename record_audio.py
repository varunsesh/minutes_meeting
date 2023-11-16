import openai
import pyaudio
import wave
import os


def transcribe_audio(client):
    # Initialize the PyAudio object
    p = pyaudio.PyAudio()

    # Open a microphone stream
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)

    # Create a WAV file to temporarily store audio data
    wav_filename = "temp.wav"
    wav_file = wave.open(wav_filename, "wb")
    wav_file.setnchannels(1)
    wav_file.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wav_file.setframerate(16000)

    # Initialize the OpenAI API client
    transcription_file = "transcription.txt"
    try:
        while True:
            print("Listening... (Press Ctrl+C to stop)")
            audio_data = stream.read(1024)
            wav_file.writeframes(audio_data)

    except KeyboardInterrupt:
        pass
    finally:
        wav_file.close()

        with open(wav_filename, "rb") as audio_file:
            print("Here now opening audio file")
            transcript = client.audio.transcriptions.create(model="whisper-1",file=audio_file)
 # Print the transcription
        print("Transcription:", transcript)
        with open(transcription_file, "a") as transcript_file:
          transcript_file.write(transcript.text)
 # Reset the WAV file for the next audio chunk
        wav_file = wave.open(wav_filename, "wb")
        wav_file.setnchannels(1)
        wav_file.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wav_file.setframerate(16000)
        # Close the audio stream and terminate PyAudio
        stream.stop_stream()
        stream.close()
        p.terminate()

        # Close and remove the temporary WAV file
        wav_file.close()
        os.remove(wav_filename)

    return transcript.text 

