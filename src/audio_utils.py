import atexit
import os
import platform
import subprocess
import re
import logging
import sys
import zipfile
from PyQt5.QtWidgets import QApplication, QMessageBox
import webbrowser
import ctypes
import sys
import pyaudio

import requests

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def setup_logging():
    """Setup the logging configuration."""
    logging.basicConfig(level=logging.INFO)

def is_voicemeeter_installed():
    import winreg
    try:
        registry_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\VoiceMeeter_Key"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0, winreg.KEY_READ):
            return True
    except FileNotFoundError:
        return False
    
def run_as_admin(argv=None, debug=False):
    shell32 = ctypes.windll.shell32
    if argv is None and shell32.IsUserAnAdmin():
        # Already running as admin
        return True

    if argv is None:
        argv = sys.argv

    if hasattr(sys, '_MEIPASS'):
        arguments = map(str, argv[1:])
    else:
        arguments = map(str, argv)

    argument_line = u' '.join(arguments)
    executable = str(sys.executable)
    if debug:
        print("Command line: ", executable, argument_line)
    ret = shell32.ShellExecuteW(None, "runas", executable, argument_line, None, 1)
    if int(ret) <= 32:
        return False
    return None

def install_voicemeeter():
    msgBox = QMessageBox()
    msgBox.setIcon(QMessageBox.Question)
    msgBox.setText("Voicemeeter is not installed. Do you want to install it now?")
    msgBox.setWindowTitle("Install Voicemeeter")
    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    if msgBox.exec() == QMessageBox.Yes:
        if not is_admin():
            run_as_admin()
        else:
            # Download and install Voicemeeter
            voicemeeter_url = "https://download.vb-audio.com/Download_CABLE/VoicemeeterSetup_v1088.zip"
            download_path = "VoicemeeterSetup.zip"
            extraction_path = "Voicemeeter_Installation"

            response = requests.get(voicemeeter_url)
            with open(download_path, 'wb') as file:
                file.write(response.content)

            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(extraction_path)
        
            # Assuming the installer is an .exe file inside the zip
            installer_path = os.path.join(extraction_path, "VoicemeeterSetup.exe")
            subprocess.run(installer_path, shell=True)

def configure_voicemeeter():
    instructions = (
    "Set Voicemeeter as the Default Recording Device:\n"
    "1. Right-click on the sound icon in your system tray and select 'Sounds'.\n"
    "2. Go to the 'Recording' tab.\n"
    "3. Find Voicemeeter Output, right-click on it, and set it as the default device.\n\n"
    "Configure Voicemeeter:\n"
    "1. Open Voicemeeter.\n"
    "2. For the hardware input, select your microphone.\n"
    "3. For the hardware out, select your main speakers or headphones.\n"
    "4. Adjust the input and output levels to avoid feedback or distortion.\n\n"
    "Routing Audio from Speakers to Microphone:\n"
    "1. In Voicemeeter, route your microphone to one of the virtual outputs (B1 or B2).\n"
    "2. Then, select the same virtual output (B1 or B2) as the input in the application "
    "where you want the audio to be sent (like a recording software or a communication app).\n\n"
    "Preventing Playback Through Speakers:\n"
    "1. To prevent playback through speakers, ensure that the virtual output (B1 or B2) used "
    "for routing the microphone is not also set as an output on the Voicemeeter.\n\n"
)

    QMessageBox.information(None, "Configure Voicemeeter", instructions)

def check_voicemeeter_set_as_default():
    pa = pyaudio.PyAudio()
    try:
        default_device_index = pa.get_default_input_device_info()['index']
        device_info = pa.get_device_info_by_index(default_device_index)
        return "VoiceMeeter" in device_info.get('name')
    finally:
        pa.terminate()

def prompt_for_default_device_setting():
    QMessageBox.warning(None, "Configure Recording Device", 
                        "VoiceMeeter is not set as the default recording device. "
                        "Please open Sound Settings and set it as the default device.",
                        QMessageBox.Ok)
    webbrowser.open("ms-settings:sound")
    
def handle_windows_audio(audio_utils):
    if not is_voicemeeter_installed():
        install_voicemeeter()
        configure_voicemeeter()
    elif not check_voicemeeter_set_as_default():
        prompt_for_default_device_setting()

class AudioUtils:
    def __init__(self):
        self.loaded_modules = []

    def run_subprocess(self, command: list) -> str:
        """Run a subprocess command and return its output as a string."""
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logging.error(f"Subprocess error: {e}")
            return None

    def load_module(self, module_name: str, args: str = "") -> None:
        """Load a PulseAudio module and track it."""
        command = f"pactl load-module {module_name} {args}".split()
        module_id = self.run_subprocess(command)
        if module_id:
            self.loaded_modules.append(module_id)
            logging.info(f"Loaded module {module_name} with ID {module_id}")

    def search_in_output(self, pattern: str, output: str) -> str:
        """Search for a pattern in the provided output and return the first matching group."""
        match = re.search(pattern, output, re.DOTALL)
        return match.group(1) if match else None

    def get_default_sink_monitor(self) -> str:
        """Get the monitor of the default PulseAudio sink."""
        output = self.run_subprocess(['pacmd', 'list-sinks'])
        if output:
            sink_name = self.search_in_output(r'\* index: \d+.*?name: <(.*?)>', output)
            if sink_name:
                return f"{sink_name}.monitor"
        return None

    def get_default_source(self) -> str:
        """Get the default PulseAudio source (input device)."""
        output = self.run_subprocess(['pacmd', 'list-sources'])
        if output:
            return self.search_in_output(r'\* index: \d+.*?name: <(.*?)>', output)
        return None

    def unload_modules(self) -> None:
        """Unload all tracked modules."""
        for module_id in self.loaded_modules:
            self.run_subprocess(["pactl", "unload-module", module_id])
            logging.info(f"Unloaded module with ID {module_id}")

    def setup_virtual_source(self) -> None:
        """Sets up a virtual source combining system output and microphone."""
        default_sink_monitor = self.get_default_sink_monitor()
        default_source = self.get_default_source()

        if default_sink_monitor and default_source:
            logging.info(f"Default sink monitor: {default_sink_monitor}, Default source: {default_source}")
            self.load_module("module-null-sink", "sink_name=virtual_sink")
            self.load_module("module-loopback", f"sink=virtual_sink source={default_source}")
            self.load_module("module-loopback", f"sink=virtual_sink source={default_sink_monitor}")
            self.run_subprocess(["pacmd", "set-default-source", "virtual_sink.monitor"])
        else:
            logging.error("Could not find default sink monitor or source.")

def audio_setup():
    """Set up the audio based on the operating system."""
    os_name = platform.system()
    app = QApplication(sys.argv)
    audio_utils = AudioUtils()

    if os_name == "Linux":
        audio_utils.setup_virtual_source()
    elif os_name == "Windows":
        handle_windows_audio(audio_utils)

    atexit.register(audio_utils.unload_modules)

if __name__ == "__main__":
    setup_logging()
    audio_setup()
