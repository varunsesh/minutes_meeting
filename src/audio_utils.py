import atexit
import ctypes
import logging
import os
import platform
import pyaudio
import re
import requests
import subprocess
import sys
import zipfile
from PyQt5.QtWidgets import QMessageBox
import webbrowser


class WindowsAudioManager:
    VOICEMEETER_URL = "https://download.vb-audio.com/Download_CABLE/VoicemeeterSetup_v1088.zip"
    DOWNLOAD_PATH = "VoicemeeterSetup.zip"
    EXTRACTION_PATH = "Voicemeeter_Installation"

    @staticmethod
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    @staticmethod
    def is_voicemeeter_installed():
        import winreg
        app_name="voicemeeter"
        paths = [r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"]
        try:
            for path in paths:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                    for i in range(0, winreg.QueryInfoKey(key)[0]):
                        skey_name = winreg.EnumKey(key, i)
                        skey = winreg.OpenKey(key, skey_name)
                        try:
                            name, _ = winreg.QueryValueEx(skey, "DisplayName")
                            if app_name.lower() in name.lower():
                                return True
                        except OSError:
                            pass
                        finally:
                            skey.Close()
            return False
        except PermissionError:
            print("Permission Denied. Run as Administrator.")
            return False

    def run_as_admin(self, argv=None, debug=False):
        if argv is None:
            argv = sys.argv

        argument_line = ' '.join(argv[1:])
        executable = sys.executable
        if debug:
            print("Command line: ", executable, argument_line)

        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, argument_line, None, 1)
        return int(ret) > 32

    def install_voicemeeter(self):
        if not self.is_admin():
            self.run_as_admin()
        else:
            response = requests.get(self.VOICEMEETER_URL)
            with open(self.DOWNLOAD_PATH, 'wb') as file:
                file.write(response.content)

            with zipfile.ZipFile(self.DOWNLOAD_PATH, 'r') as zip_ref:
                zip_ref.extractall(self.EXTRACTION_PATH)
            
            installer_path = os.path.join(self.EXTRACTION_PATH, "VoicemeeterSetup.exe")
            subprocess.run(installer_path, shell=True)
            
    def prompt_for_default_device_setting(self):
        QMessageBox.warning(None, "Configure Recording Device", 
                            "VoiceMeeter is not set as the default recording device. "
                            "Please open Sound Settings and set it as the default device.",
                            QMessageBox.Ok)
        webbrowser.open("ms-settings:sound")

    def configure_voicemeeter(self):
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

    def check_voicemeeter_set_as_default(self):
        pa = pyaudio.PyAudio()
        try:
            default_device_index = pa.get_default_input_device_info()['index']
            device_info = pa.get_device_info_by_index(default_device_index)
            return "VoiceMeeter" in device_info.get('name')
        finally:
            pa.terminate()

    def handle_windows_audio(self):
        if not self.is_voicemeeter_installed():
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Question)
            msgBox.setText("Voicemeeter is not installed. Do you want to install it now?")
            msgBox.setWindowTitle("Install Voicemeeter")
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            if msgBox.exec() == QMessageBox.Yes:
                self.install_voicemeeter()
                self.configure_voicemeeter()
        elif not self.check_voicemeeter_set_as_default():
            self.prompt_for_default_device_setting()

def setup_logging():
    """Setup the logging configuration."""
    logging.basicConfig(level=logging.INFO)


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

    def get_module_ids(self, module_names):
        """Get the IDs of specific PulseAudio modules."""
        output = self.run_subprocess(["pactl", "list", "short", "modules"])
        if output:
            module_ids = []
            for line in output.splitlines():
                parts = line.split()
                module_id, module_name = parts[0], parts[1]
                if module_name in module_names:
                    module_ids.append(module_id)
            return module_ids
        return []

    def unload_modules(self, module_ids):
        """Unload PulseAudio modules."""
        if len(module_ids) > 0:
            for module_id in module_ids:
                try:
                    self.run_subprocess(["pactl", "unload-module", module_id])
                    logging.info(f"Unloaded module with ID {module_id}")
                except Exception as e:
                    logging.info(f"Failed", e)


    def setup_virtual_source(self) -> None:
        """Sets up a virtual source combining system output and microphone."""
        module_ids = self.get_module_ids(["module-null-sink", "module-loopback"])
        if len(module_ids) > 0:
            self.unload_modules(module_ids)
        
        default_sink_monitor = self.get_default_sink_monitor()
        default_source = self.get_default_source()

        if default_sink_monitor and default_source:
            self.load_module("module-null-sink", "sink_name=virtual_sink")
            self.load_module("module-loopback", f"sink=virtual_sink source={default_source}")
            self.load_module("module-loopback", f"sink=virtual_sink source={default_sink_monitor}")
            self.run_subprocess(["pacmd", "set-default-source", "virtual_sink.monitor"])
        else:
            logging.error("Could not find default sink monitor or source.")

def audio_setup():
    """Set up the audio based on the operating system."""
    os_name = platform.system()
    audio_utils = AudioUtils()
    if os_name == "Linux":
        audio_utils.setup_virtual_source()
        try:
            atexit.register(audio_utils.unload_modules(audio_utils.loaded_modules))
        except Exception as e:
            print("Failed to unload some modules", e)
    elif os_name == "Windows":
        print("windows")
        win_audio = WindowsAudioManager()
        win_audio.handle_windows_audio()
        
if __name__ == "__main__":
    setup_logging()
    audio_setup()
