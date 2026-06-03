import bpy

class SetupPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_setup"
    bl_category = "Auto Lip Sync"
    bl_label = "Quick Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        setup = context.scene.setup
        layout = self.layout

        layout.label(text="Dependencies")
        layout.prop(setup, "installations")

        # CPU
        cpu_icon = "CHECKMARK" if setup.cpu_installed else "ERROR"
        layout.label(
            text=f"CPU Dependencies: {'Installed' if setup.cpu_installed else 'Not Installed'}",
            icon=cpu_icon
        )

        # Install state
        if setup.installing:
            layout.label(text="Installing Dependencies...", icon="TIME")

        if setup.install_log:
            layout.label(text=setup.install_log)

        # Install logic
        needs_cpu = not setup.cpu_installed

        if not setup.installing:
            if setup.installations == "CPU_Install" and needs_cpu:
                layout.operator("als.install_dependencies", icon="IMPORT")