from transcribe import TranscriptionApp  # Update with the new name if changed
from voice_recorder import VoiceRecorder  # Update with the new name if changed
import platform
from pulseaudio_manager import setup_virtual_source
import tkinter as tk
from tkinter import messagebox
import webbrowser

def check_stereo_mix():
    from pycaw.pycaw import AudioUtilities
    devices = AudioUtilities.GetRecordingDevices()
    stereo_mix = [device for device in devices if "Stereo Mix" in device.name]

    if not stereo_mix:
        return False, "Stereo Mix not found"
    
    if stereo_mix[0].state == 1:  # State 1 means the device is active
        return True, "Stereo Mix is enabled"
    else:
        return False, "Stereo Mix is disabled"

    

if __name__ == "__main__":
    print("Starting the recorder app...")

    os_name = platform.system()
    
    if os_name == "Linux":
        setup_virtual_source()
    elif os_name == "Windows":
        result, message = check_stereo_mix()
        if not result:
            root = tk.Tk()
            root.withdraw()  # Hide the main tkinter window

            messagebox.showinfo("Stereo Mix Status", message)
            if messagebox.askyesno("Open Settings", "Do you want to open the Sound settings now?"):
                webbrowser.open("ms-settings:sound")

            root.destroy()

    recorder = VoiceRecorder()  # Updated class name
    app = TranscriptionApp(recorder)  # Updated class name
    app.mainloop()

    
