import bpy
import subprocess
import sys
import threading
import shutil
from ..core import runtime_state

# Updates SetupSettings based on dependency check
def apply_result(installed):
    setup = bpy.context.window_manager.setup
    setup.ffmpeg_installed = installed["ffmpeg"]
    setup.cpu_installed = installed["cpu"]
    # Keep refreshing if FFmpeg or CPU dependencies aren't installed
    setup.needs_refresh = not installed["ffmpeg"] or not installed["cpu"]

    print("Updating SetupSettings...")
    
    print("FFmpeg Installed: ", setup.ffmpeg_installed)
    print("CPU Installed: ", setup.cpu_installed)
    print("Needs refresh: ", setup.needs_refresh)

    return None

def apply_error():
    scene = bpy.context.scene

    if not scene:
        return None

    scene.setup.cpu_installed = False
    scene.setup.needs_refresh = False
    return None

def check_deps_thread():
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

        for pkg in cpu_required:
            found = pkg in result.lower()
            print(pkg, found)
        
        bpy.app.timers.register(lambda: apply_result(installed))

    except Exception as e:
        print(f"An error occurred: {e}")
        bpy.app.timers.register(apply_error)

    finally:
        runtime_state.CHECK_RUNNING = False

def refresh_dependency_state():
    setup = bpy.context.window_manager.setup

    if runtime_state.CHECK_RUNNING:
        return
    
    runtime_state.CHECK_RUNNING = True

    print("Refreshing dependency state...")

    print("FFmpeg Installed: ", setup.ffmpeg_installed)
    print("CPU Installed: ", setup.cpu_installed)
    print("Needs refresh: ", setup.needs_refresh)

    threading.Thread(
        target=check_deps_thread,
        daemon=True 
    ).start()