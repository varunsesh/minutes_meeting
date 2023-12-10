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
cd src/
python main.py

```

# Setup Communications on Windows and Linux

To use this app to record minutes of an online meeting, 
- In windows, enable the stereo mix option in advanced sound settings. Once enabled, ensure the input device is set to stereo mix. After this in  
    advanced sound->microphone->Properties->Listen tab set listen to this device. Please note this is still not perfect, you will here an echo of your voice through the speakers, the goal is to minimise this echo to acceptable levels. Contributions to this are welcome.

- In Linux, Make sure microphone and speaker are set properly in sound settings.



