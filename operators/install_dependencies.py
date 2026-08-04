import bpy
import sys
import subprocess
from pathlib import Path
from ..core.install_monitor import monitor_install
from ..core import runtime_state

class InstallDependenciesOperator(bpy.types.Operator):
    bl_idname = "setup.install_dependencies"
    bl_label = "Install Dependencies"

    def execute(self, context):
        setup = context.window_manager.setup

        addon_root = Path(__file__).parent.parent
        requirements_path = addon_root / "requirements" / "cpu_requirements.txt"

        # Add-on owned package dir
        dependencies = addon_root / "dependencies"
        dependencies.mkdir(exist_ok=True)

        print("Installing packages to: ", dependencies)

        command = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--target",
            str(dependencies),
            "-r",
            str(requirements_path)
        ]

        print("Command: ", command)

        setup.installing = True
        setup.install_log = "Starting installation..."

        runtime_state.INSTALL_PROCESS = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        bpy.app.timers.register(monitor_install)

        self.report({'INFO'}, "Dependency installation started")

        return {'FINISHED'}
