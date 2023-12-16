# Minutes of the Meeting
Record meeting using Whisper and generate minutes using OpenAI APIs.

## Table of Contents
1. [Setup](#setup)
2. [Requirements](#requirements)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [Build Instructions](#build-instructions)
6. [Logging](#logging)

## Setup

To Setup and run this application, follow these steps:

1. **Clone the Repository**:
   ```bash
   git clone git@github.com:varunsesh/minutes_meeting.git
   cd minutes_meeting


2. **Setup Python Environment(Optional)**:
    - Use a virtual environment for better isolation:
    ```
    python -m venv env 
    source env/bin/activate # On Windows use env\\Scripts\\activate
    ```
## Requirements

Make sure you have Python installed on your system. Then install the required dependencies:

```
pip install -r requirements.txt
```

## Usage

Navigate to the `src/` directory and run the application:
    
```
cd src/
python cli.py

```

## Configuration

1. **Set .env and config**:
    - Update your OpenAI API key in the `.env` file.
    - Add Google config.json credentials to src/config folder.

2. **Setup Communications on Windows and Linux**

    To use this app to record, 

    - In Windows, ensure the microphone is set to VoiceMeeter and that VoiceMeeter is configured correctly. Follow the in-app instructions for setup to avoid recording issues.

    - In Linux, Make sure microphone and speaker are set properly in sound settings, before starting the app. Don't change settings after starting the app.

## Build Instructions

Ensure all dependencies are installed as per the 'requirements.txt'.

1. **Linux**:

    Use PyInstaller to create an executable:

    ```
    pyinstaller --add-data=".env:." --add-data="src/config:src/config" --add-data="src/assets:src/assets" --collect-all="whisper" --collect-all="nvidia" cli.py
    ```

2. **Windows**: 

    
    Use PyInstaller with the following command (adjust paths if necessary):

    ```
    pyinstaller --add-data=".env;." --add-data="src\config;src\config" --add-data="src\assets;src\assets" --collect-all="whisper" --collect-all="nvidia" cli.py
    ```
## Logging

All log messages are logged to logs/Minutes.log

If you want to see logs in console then uncomment part of code in __main.py__.
 
 ```    # console handler to print the logs
        # console_handler = logging.StreamHandler()
        # console_handler.setLevel(logging.INFO)
        # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # console_handler.setFormatter(formatter)
        # logging.getLogger('').addHandler(console_handler)
 ```



