import bpy
import threading
import importlib.util
import shutil
import traceback
from ..core import runtime_state

# Updates SetupSettings based on dependency check
def apply_result(installed):
    print("installed =", installed)

    setup = bpy.context.window_manager.setup
  
    setup.ffmpeg_installed = installed["ffmpeg"] is not None
    setup.cpu_installed = installed["cpu"]

    # Keep refreshing if FFmpeg or CPU dependencies aren't installed
    if not setup.ffmpeg_installed or not setup.cpu_installed:
        bpy.app.timers.register(refresh_dependency_state, first_interval=1.0)

    runtime_state.CHECK_RUNNING = False
    return None

# Handles case where checking dependencies fails
def apply_error():
    runtime_state.CHECK_RUNNING = False

    wm = bpy.context.window_manager
    if not wm:
        return None
    
    return None

# Checks for required FFmpeg and CPU dependencies
def check_deps_thread():
    try:
        installed = {}

        # Check if FFmpeg is installed on the user's machine
        installed["ffmpeg"] = shutil.which("ffmpeg")

        # Check if add-on can import CPU dependencies
        cpu_required = [
            "whisperx", 
            "phonemizer", 
            "tokenizers", 
            "transformers", 
            "huggingface_hub",
            "torch",
            "torchaudio",
            "ctranslate2",
            "faster_whisper",
            "pyannote",
            "omegaconf",
            "nltk"
        ]
    
        installed["cpu"] = all(
            importlib.util.find_spec(pkg) is not None
            for pkg in cpu_required
        )

        # Register apply_result so Blender later calls it to update SetupSettings
        bpy.app.timers.register(lambda: apply_result(installed))

    except Exception as e:
        print(f"An error occurred: {e}")
        apply_error()
        traceback.print_exc()

# Executes thread to update dependencies state
def refresh_dependency_state():
    if runtime_state.CHECK_RUNNING:
        return
    
    runtime_state.CHECK_RUNNING = True

    threading.Thread(
        target=check_deps_thread,
        daemon=True 
    ).start()