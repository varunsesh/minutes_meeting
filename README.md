# Minutes of the Meeting (courtesy OpenAI)
Record meeting using whisper and generate minutes using openAI apis

# Instructions for Deployment
- Update open api key in .env file
- Run the python environment in a venv with 
```
python -m venv .
```
```
pip install -r requirements.txt
```
```
python speech2text.py
```

# Setup Communications on Windows

To use this app to record minutes of an online meeting, in windows, enable the stereo mix option in advanced sound settings. Once enabled, ensure the input device is set to stereo mix. After this in advanced sound->microphone->Properties->Listen tab set listen to this device. 

Reduce the microphone level in the levels tab in microphone properties to minimise the echo through the speakers.

Please note this is still not perfect, you will here an echo of your voice through the speakers, the goal is to minimise this echo to acceptable levels.



