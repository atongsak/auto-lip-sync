import bpy
import sys
import subprocess
from pathlib import Path
from ..core.install_monitor import monitor_install

class InstallDependenciesOperator(bpy.types.Operator):
    bl_idname = "als.install_dependencies"
    bl_label = "Install Dependencies"

    def execute(self, context):
        global INSTALL_PROCESS, INSTALL_SCENE

        setup = context.scene.setup

        addon_root = Path(__file__).parent.parent
        requirements_path = addon_root / "requirements" / "cpu_requirements.txt"

        python_exe = sys.executable

        command = [python_exe, "-m", "pip", "install", "-r", str(requirements_path)]

        setup.installing = True
        setup.install_log = "Starting installation..."

        # Installs into Blender's bundled Python environment
        INSTALL_PROCESS = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        INSTALL_SCENE = context.scene

        bpy.app.timers.register(monitor_install)

        self.report({'INFO'}, "Dependency installation started")

        return {'FINISHED'}
