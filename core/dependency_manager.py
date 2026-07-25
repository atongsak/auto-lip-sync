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
    print("after ffmpeg:", setup.ffmpeg_installed)

    setup.cpu_installed = installed["cpu"]
    print("after cpu:", setup.cpu_installed)

    # Keep refreshing if FFmpeg or CPU dependencies aren't installed
    setup.needs_refresh = (not setup.ffmpeg_installed or not setup.cpu_installed)
    print("after refresh:", setup.needs_refresh)

    print("Updating SetupSettings...")
    
    print("FFmpeg Installed: ", setup.ffmpeg_installed)
    print("CPU Installed: ", setup.cpu_installed)
    print("Needs refresh: ", setup.needs_refresh)

    runtime_state.CHECK_RUNNING = False
    return None

# TODO: Do I really need this
def apply_error():
    wm = bpy.context.window_manager

    if not wm:
        return None

    wm.setup.cpu_installed = False
    wm.setup.needs_refresh = False
    return None

def finish(installed):
    print("Timer executing")
    apply_result(installed)
    return None

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
        
        bpy.app.timers.register(lambda: finish(installed))

    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()

def refresh_dependency_state():
    print("refresh dep state")

    if runtime_state.CHECK_RUNNING:
        return
    
    runtime_state.CHECK_RUNNING = True

    # print("Refreshing dependency state...")

    # print("FFmpeg Installed: ", setup.ffmpeg_installed)
    # print("CPU Installed: ", setup.cpu_installed)
    # print("Needs refresh: ", setup.needs_refresh)

    threading.Thread(
        target=check_deps_thread,
        daemon=True 
    ).start()