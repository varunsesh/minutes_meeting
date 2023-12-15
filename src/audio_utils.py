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
    VOICEMEETER_CONFIG_PATH = os.path.join(os.path.expanduser('~'), 'Documents/Voicemeeter')

    @staticmethod
    def is_admin():
        """
        Check if the current user is an administrator on the system.

        Returns:
            True if the current user is an administrator, False otherwise.
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    @staticmethod
    def is_voicemeeter_installed():
        """
        Check if the current user is an administrator on the system.

        Returns:
            True if the current user is an administrator, False otherwise.
        """
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
                            logging.error('OSError')
                        finally:
                            skey.Close()
            return False
        except PermissionError:
            logging.error("Permission Denied. Run as Administrator.")
            return False

    def run_as_admin(self, argv=None, debug=False):
        if argv is None:
            argv = sys.argv

        argument_line = ' '.join(argv[1:])
        executable = sys.executable
        if debug:
            logging.info("Command line: ", executable, argument_line)

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
    
    def configure_voicemeeter(self):
        import shutil
        config_path = os.path.join(self.VOICEMEETER_CONFIG_PATH, 'VoicemeeterStandard_LastSettings.xml')

        if not os.path.exists(self.VOICEMEETER_CONFIG_PATH):
            os.makedirs(self.VOICEMEETER_CONFIG_PATH)
        shutil.copy("config/VoicemeeterStandard_LastSettings.xml", config_path)
        logging.info(f"Voicemeeter Configured Successfully")

            
    def prompt_for_default_device_setting(self):
        instructions = (
            "Setting Up Voicemeeter as Default Recording Device:\n"
            "1. Open 'Sounds'.\n"
            "2. Navigate to the 'Recording' tab.\n"
            "3. Locate 'Voicemeeter Output', right-click it, and select 'Set as Default Device'.\n\n"
            "Configuring Voicemeeter Settings:\n"
            "1. Launch Voicemeeter.\n"
            "2. Click on Menu and Check System Tray and Run on Windows Startup.\n"
            "4. Assign Voicemeeter as your primary microphone and retain the system speakers as the default output device.\n"
            f"5. If you face any issues with recording just load the configuration file from {self.VOICEMEETER_CONFIG_PATH}.\n"
        )
        QMessageBox.information(None, "Configure Recording Device", instructions, QMessageBox.Ok)
        webbrowser.open("ms-settings:sound")

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


class LinuxAudioManager:

    def run_subprocess(self, command: list) -> str:
        """Run a subprocess command and return its output as a string."""
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logging.error(f"Subprocess error: {e}")
            return None
        except Exception as e:
            logging.info(f"Pulse Audio errors: {e}")

    def load_module(self, module_name: str, args: str = "") -> None:
        """Load a PulseAudio module and track it."""
        command = f"pactl load-module {module_name} {args}".split()
        self.run_subprocess(command)

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
        # clean up any null-sinks
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
    
    if os_name == "Linux":
        linux_audio = LinuxAudioManager()
        linux_audio.setup_virtual_source()
    
    elif os_name == "Windows":
        win_audio = WindowsAudioManager()
        win_audio.handle_windows_audio()
        
if __name__ == "__main__":
    audio_setup()
