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

        installed = ("whisperx" in result and "phonemizer" in result)

        # IMPORTANT: avoid writing bpy data from thread directly
        def apply_result():
            if setup:
                setup.cpu_installed = installed
                setup.needs_refresh = False
            return None

        bpy.app.timers.register(apply_result)

    except Exception as e:
        def apply_error():
            if setup:
                setup.cpu_installed = False
                setup.needs_refresh = False
            return None

        bpy.app.timers.register(apply_error)

    setup.cpu_installed = all(pkg in result.lower() for pkg in ["whisperx", "phonemizer"])
    setup.needs_refresh = False

def refresh_dependency_state(scene):
    if not scene or not hasattr(scene, "setup"):
        return

    # prevent spam re-threads
    if getattr(scene.setup, "needs_refresh", False) is False:
        return

    threading.Thread(
        target=check_deps_thread,
        args=(scene.setup,),
        daemon=True  # IMPORTANT
    ).start()