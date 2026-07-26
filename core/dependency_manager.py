import bpy
import subprocess
import sys
import threading
import shutil
import traceback
from ..core import runtime_state

# Updates SetupSettings based on dependency check
def apply_result(installed):
    print("apply result")
    print("installed =", installed)

    setup = bpy.context.window_manager.setup
  
    setup.ffmpeg_installed = installed["ffmpeg"] is not None
    setup.cpu_installed = installed["cpu"]

    # Keep refreshing if FFmpeg or CPU dependencies aren't installed
    if not setup.ffmpeg_installed or not setup.cpu_installed:
        bpy.app.timers.register(refresh_dependency_state, first_interval=2.0)

    print("Updating SetupSettings...")
    print("FFmpeg Installed: ", setup.ffmpeg_installed)
    print("CPU Installed: ", setup.cpu_installed)

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
    print("thread started")
    try:
        installed = {}

        # Check if FFmpeg is installed on the user's machine
        installed["ffmpeg"] = shutil.which("ffmpeg")

        # Check needed dependencies in site-packages
        result = subprocess.check_output(
            [sys.executable, "-m", "pip", "list"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8").lower()

        cpu_required = [
            "whisperx", 
            "phonemizer", 
            "tokenizers", 
            "transformers", 
            "huggingface_hub",
            "py-espeak-ng"
        ]
        
        installed["cpu"] = all(pkg in result for pkg in cpu_required)

        # Register apply_result so Blender later calls it to update SetupSettings
        bpy.app.timers.register(lambda: apply_result(installed))

    except Exception as e:
        print(f"An error occurred: {e}")
        apply_error()
        traceback.print_exc()

# Executes thread to update dependencies state
def refresh_dependency_state():
    print("refresh dep state")
    print("check running ", runtime_state.CHECK_RUNNING)

    if runtime_state.CHECK_RUNNING:
        print("returning")
        return
    
    runtime_state.CHECK_RUNNING = True

    threading.Thread(
        target=check_deps_thread,
        daemon=True 
    ).start()