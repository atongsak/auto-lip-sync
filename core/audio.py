import bpy
import os
import time

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

        # Remove an old file so we don't detect it as the new WAV
        if os.path.exists(output_path):
            os.remove(output_path)

        # Create wav of rendered audio in target channel
        bpy.ops.sound.mixdown(
            filepath=output_path,
            container='WAV',
            codec='PCM',
            format='S16'
        )

        # Wait until WAV size is stable
        last_size = -1

        while True:
            if os.path.exists(output_path):
                size = os.path.getsize(output_path)
                if size > 0 and size == last_size:
                    break
                last_size = size
            time.sleep(0.1)

    finally:  
        # Revert mute states of strips in VSE
        for strip in scene.sequence_editor.strips_all:
            strip.mute = original_mute_states[strip.name]

    return output_path