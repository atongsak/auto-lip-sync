import bpy
import importlib
import subprocess
import sys

import threading

def check_deps_thread(setup):
    try:
        result = subprocess.check_output(
            [sys.executable, "-m", "pip", "list"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8").lower()

        print("Python:", sys.executable)
        print(result)

        installed = ("whisperx" in result and "phonemizer" in result)

        cpu_required = ["whisperx", "phonemizer"]
        for pkg in cpu_required:
            found = pkg in result.lower()
            print(pkg, found)

        # Updates SetupSettings based on dependency check
        def apply_result():
            if setup:
                setup.cpu_installed = installed
                setup.needs_refresh = not installed
            return None

        bpy.app.timers.register(apply_result)

    except Exception as e:
        def apply_error():
            if setup:
                setup.cpu_installed = False
                setup.needs_refresh = False
            return None

        bpy.app.timers.register(apply_error)

def refresh_dependency_state(scene):
    print("Refreshing dependency state...")
    if not scene or not hasattr(scene, "setup"):
        return

    print("CPU Installed =", scene.setup.cpu_installed)

    # # prevent spam re-threads
    # if getattr(scene.setup, "needs_refresh", False) is False:
    #     return

    threading.Thread(
        target=check_deps_thread,
        args=(scene.setup,),
        daemon=True 
    ).start()