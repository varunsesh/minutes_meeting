import atexit
import subprocess
import re
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

loaded_modules = []

def run_subprocess(command: list) -> str:
    """Run a subprocess command and return its output as a string."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Subprocess error: {e}")
        return None

def load_module(module_name: str, args: str = "") -> None:
    """Load a PulseAudio module and track it."""
    command = f"pactl load-module {module_name} {args}".split()
    module_id = run_subprocess(command)
    if module_id:
        loaded_modules.append(module_id)
        logging.info(f"Loaded module {module_name} with ID {module_id}")

def search_in_output(pattern: str, output: str) -> str:
    """Search for a pattern in the provided output and return the first matching group."""
    match = re.search(pattern, output, re.DOTALL)
    return match.group(1) if match else None

def get_default_sink_monitor() -> str:
    """Get the monitor of the default PulseAudio sink."""
    output = run_subprocess(['pacmd', 'list-sinks'])
    if output:
        sink_name = search_in_output(r'\* index: \d+.*?name: <(.*?)>', output)
        if sink_name:
            return f"{sink_name}.monitor"
    return None

def get_default_source() -> str:
    """Get the default PulseAudio source (input device)."""
    output = run_subprocess(['pacmd', 'list-sources'])
    if output:
        return search_in_output(r'\* index: \d+.*?name: <(.*?)>', output)
    return None

def unload_modules() -> None:
    """Unload all tracked modules."""
    for module_id in loaded_modules:
        run_subprocess(["pactl", "unload-module", module_id])
        logging.info(f"Unloaded module with ID {module_id}")

def setup_virtual_source() -> None:
    """Sets up a virtual source combining system output and microphone."""
    default_sink_monitor = get_default_sink_monitor()
    default_source = get_default_source()

    if default_sink_monitor and default_source:
        logging.info(f"Default sink monitor: {default_sink_monitor}, Default source: {default_source}")
        load_module("module-null-sink", "sink_name=virtual_sink")
        load_module("module-loopback", f"sink=virtual_sink source={default_source}")
        load_module("module-loopback", f"sink=virtual_sink source={default_sink_monitor}")
        run_subprocess(["pacmd","set-default-source","virtual_sink.monitor"])
    else:
        logging.error("Could not find default sink monitor or source.")
    atexit.register(unload_modules)

def main() -> None:
    """Main function to set up virtual source."""
    setup_virtual_source()

if __name__ == "__main__":
    main()
