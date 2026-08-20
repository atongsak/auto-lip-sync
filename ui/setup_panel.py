import bpy
import shutil

class SetupPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_setup"
    bl_category = "Auto Lip Sync"
    bl_label = "Dependency Checker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        setup = context.window_manager.setup
        layout = self.layout

        # FFmpeg
        ffmpeg_icon = "CHECKMARK" if setup.ffmpeg_installed else "ERROR"
        layout.label(
            text=f"FFmpeg: {'Installed' if setup.ffmpeg_installed else 'Not Installed'}",
            icon=ffmpeg_icon
        )

        # eSpeak NG
        espeak = shutil.which("espeak-ng")
        layout.label(
            text=f"eSpeak NG: {'Installed' if espeak else 'Not Installed'}",
            icon="CHECKMARK" if espeak else "ERROR"
        )

        # CPU
        cpu_icon = "CHECKMARK" if setup.cpu_installed else "ERROR"
        layout.label(
            text=f"CPU Dependencies: {'Installed' if setup.cpu_installed else 'Not Installed'}",
            icon=cpu_icon
        )