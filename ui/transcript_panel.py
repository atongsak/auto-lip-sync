import bpy
import textwrap

# Splits and wraps a long string into multiple layout.label() rows
# Dynamically responds to the width of the Blender UI panel
def draw_multiline_label(context, layout, text):
    # Approximate char width based on the region's pixel width
    panel_width = context.region.width
    calculated_width = max(10, int(panel_width / 14))

    wrapper = textwrap.TextWrapper(width=calculated_width)
    wrapped_lines = wrapper.wrap(text=text)

    # Draw each line as a separate UI element
    for line in wrapped_lines:
        layout.label(text=line)

class TranscriptPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_transcript"
    bl_category = "Auto Lip Sync"
    bl_label = "Detected Transcript"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        settings = context.scene.auto_lip_sync
        layout = self.layout

        transcript_icon = "CHECKMARK" if settings.detected_transcript else "ERROR"
        transcript_header = ""

        if settings.detected_transcript:
            transcript_header = "Audio transcribed successfully"
        elif settings.is_generating:
            transcript_header = "Currently transcribing audio"
        else:
            transcript_header = "No words detected"

        layout.label(
            text=transcript_header,
            icon=transcript_icon
        )

        if settings.detected_transcript:
            box = layout.box()
            draw_multiline_label(context, box, settings.detected_transcript)