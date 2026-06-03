import bpy
import os

# Returns file path to created target channel audio wav 
def get_target_audio_path(context):
    scene = context.scene
    target_channel = int(scene.auto_lip_sync.target_channel)

    original_mute_states = {}

    try:
        for strip in scene.sequence_editor.strips_all:
            # Save original mute states of strips in VSE
            original_mute_states[strip.name] = strip.mute

            # Mute strips that aren't in target channel
            if strip.channel != target_channel:
                strip.mute = True
    
        output_path = os.path.join(bpy.app.tempdir, "target_audio.wav")

        # Create wav of rendered audio in target channel
        bpy.ops.sound.mixdown(
            filepath=output_path,
            container='WAV',
            codec='PCM',
            format='S16'
        )

    finally:  
        # Revert mute states of strips in VSE
        for strip in scene.sequence_editor.strips_all:
            strip.mute = original_mute_states[strip.name]

    return output_path