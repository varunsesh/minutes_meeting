import atexit
import platform
import subprocess
import re
import logging
import tkinter as tk
from tkinter import messagebox
import webbrowser

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

def check_stereo_mix() -> tuple:
    """Check if Stereo Mix is available and enabled."""
    from pycaw.pycaw import AudioUtilities
    devices = AudioUtilities.GetRecordingDevices()
    stereo_mix = [device for device in devices if "Stereo Mix" in device.name]

    if not stereo_mix:
        return False, "Stereo Mix not found"
    
    return (stereo_mix[0].state == 1, "Stereo Mix is enabled" if stereo_mix[0].state == 1 else "Stereo Mix is disabled")

def audio_setup():
    """Set up the audio based on the operating system."""
    os_name = platform.system()
    audio_utils = AudioUtils()

    if os_name == "Linux":
        audio_utils.setup_virtual_source()
    elif os_name == "Windows":
        result, message = check_stereo_mix()
        if not result:
            root = tk.Tk()
            root.withdraw()  # Hide the main tkinter window

            messagebox.showinfo("Stereo Mix Status", message)
            if messagebox.askyesno("Open Settings", "Do you want to open the Sound settings now?"):
                webbrowser.open("ms-settings:sound")

            root.destroy()
    atexit.register(audio_utils.unload_modules)

if __name__ == "__main__":
    setup_logging()
    audio_setup()
