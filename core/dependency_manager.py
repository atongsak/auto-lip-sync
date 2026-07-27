import bpy
import subprocess
import sys
import threading
import importlib.util
from pathlib import Path
import shutil
import traceback
import platform
from ..core import runtime_state

# Updates SetupSettings based on dependency check
def apply_result(installed):
    # print("apply result")
    # print("installed =", installed)

    setup = bpy.context.window_manager.setup
  
    setup.ffmpeg_installed = installed["ffmpeg"] is not None
    setup.cpu_installed = installed["cpu"]

    # Keep refreshing if FFmpeg or CPU dependencies aren't installed
    if not setup.ffmpeg_installed or not setup.cpu_installed:
        bpy.app.timers.register(refresh_dependency_state, first_interval=2.0)

    # print("Updating SetupSettings...")
    # print("FFmpeg Installed: ", setup.ffmpeg_installed)
    # print("CPU Installed: ", setup.cpu_installed)

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
    # print("thread started")

    try:
        # print("in try")
        installed = {}

        # Check if FFmpeg is installed on the user's machine
        installed["ffmpeg"] = shutil.which("ffmpeg")

        # Check if add-on can import CPU dependencies

        if platform.system() == "Windows":
            cpu_required = [
                "whisperx", 
                "phonemizer", 
                "tokenizers", 
                "transformers", 
                "huggingface_hub"
            ]

        elif platform.system() == "Darwin":
            cpu_required = [
                "whisperx", 
                "phonemizer", 
                "tokenizers", 
                "transformers", 
                "huggingface_hub",
                "py_espeak_ng"
            ]

        pkg = Path(sys.path[0])

        for name in cpu_required:
            print("\n", name)
            print("folder exists:", (pkg / name).exists())
            print("spec:", importlib.util.find_spec(name))

        # for item in pkg.iterdir():
        #     if "espeak" in item.name.lower():
        #         print(item)

        
        installed["cpu"] = all(
            importlib.util.find_spec(pkg) is not None
            for pkg in cpu_required
        )

        print(installed["cpu"])

        # Register apply_result so Blender later calls it to update SetupSettings
        bpy.app.timers.register(lambda: apply_result(installed))

    except Exception as e:
        print(f"An error occurred: {e}")
        apply_error()
        traceback.print_exc()

# Executes thread to update dependencies state
def refresh_dependency_state():
    # print("refresh dep state")
    # print(sys.path)
    if runtime_state.CHECK_RUNNING:
        # print("returning")
        return
    
    runtime_state.CHECK_RUNNING = True

    threading.Thread(
        target=check_deps_thread,
        daemon=True 
    ).start()