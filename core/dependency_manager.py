import bpy
import subprocess
import sys
import threading
from ..core import runtime_state

# Updates SetupSettings based on dependency check
def apply_result(installed):
    scene = bpy.context.scene

    if not scene:
        return None
    
    setup = scene.setup
    setup.cpu_installed = installed
    setup.needs_refresh = not installed

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
        result = subprocess.check_output(
            [sys.executable, "-m", "pip", "list"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8").lower()

        print("Python:", sys.executable)
        print(result)

        cpu_required = [
            "whisperx", 
            "phonemizer", 
            "tokenizers", 
            "transformers", 
            "huggingface_hub",
            "py-espeak-ng"
        ]

        installed = all(pkg in result for pkg in cpu_required)

        for pkg in cpu_required:
            found = pkg in result.lower()
            print(pkg, found)
        
        bpy.app.timers.register(lambda: apply_result(installed))

    except Exception as e:
        bpy.app.timers.register(apply_error)

    finally:
        runtime_state.CHECK_RUNNING = False

def refresh_dependency_state(scene):
    if runtime_state.CHECK_RUNNING:
        return
    
    runtime_state.CHECK_RUNNING = True

    print("Refreshing dependency state...")

    print("CPU Installed: ", scene.setup.cpu_installed)
    print("Needs refresh: ", scene.setup.needs_refresh)

    threading.Thread(
        target=check_deps_thread,
        daemon=True 
    ).start()