import bpy
import os
import json
import sys
import subprocess
import queue
import threading
import re
from bpy_extras import anim_utils
from pathlib import Path
from ..core.visemes import get_mapped_visemes
from ..core.audio import get_target_audio_path
from ..core.ffmpeg_path import get_ffmpeg_path

class AudioToVisemeOperator(bpy.types.Operator): 
    bl_idname = "wm.run_subprocess"
    bl_label = "Function that runs the audio-to-viseme process"     
            
    # Writes settings.json, starts subprocess, starts timer/modal loop
    def execute(self, context):
        settings = context.scene.auto_lip_sync
        settings.is_generating = True
        settings.progress = 0.0
        
        mapped_visemes_dict = get_mapped_visemes(context)
        target_audio_path = get_target_audio_path(context)
        
        # Check file size of target channel audio wav
        file_size = os.path.getsize(target_audio_path)
        limit_bytes = 25 * 1024 * 1024 # Whisper can handle files <25 MB
        
        if file_size > limit_bytes:
            self.report(
                {'WARNING'}, 
                f"Rendered audio in target channel exceeds 25 MB ({file_size} bytes)."
            )
            return {'CANCELLED'}
        
        settings_dict = {
            "fps": context.scene.render.fps,
            "render_start": context.scene.frame_start,
            "render_end": context.scene.frame_end,
            "viseme_set": settings.viseme_set,
            "model_size": settings.model_size,
            "mouth_close_delay": settings.mouth_close_delay,
            "audio_path": target_audio_path,
            "visemes": mapped_visemes_dict
        }

        addon_root = Path(__file__).parent.parent

        # Copy the user's current env vars into new dict
        env = os.environ.copy()
        ffmpeg_dir = get_ffmpeg_path()
        print(ffmpeg_dir.exists())
        print((ffmpeg_dir / "ffmpeg.exe").exists())

        # Prepend ffmpeg dir to the search paths
        env["PATH"] = str(ffmpeg_dir) + os.pathsep + env["PATH"]

        temp_dir = Path(bpy.app.tempdir)
        settings_path = temp_dir / "settings.json"

        print(bpy.app.tempdir)

        with open(settings_path, 'w', encoding='utf-8') as f:
            text = json.dumps(settings_dict, indent=4)
            f.write(text)

        pipeline_script = addon_root / "pipeline" / "main.py"
        
        python_exe = sys.executable
        command = [python_exe, "-u", str(pipeline_script), "--", "--file", str(settings_path), "--compute", settings.compute]

        self.process = subprocess.Popen(
                        command,
                        env=env,
                        # stdout = subprocess.PIPE, # Save command's output into var instead of printing
                        # stderr = subprocess.STDOUT,
                        text = True
                    )
        
        # self.queue = queue.Queue()
                        
        # def enqueue_output(pipe, q):
        #     for line in iter(pipe.readline, ''):
        #         q.put(line)
        #     pipe.close()
            
        # Create thread to read progress logs from main.py
        # self.thread = threading.Thread(
        #     target=enqueue_output,
        #     args=(self.process.stdout, self.queue),
        #     daemon=True
        # )
        # self.thread.start()
                    
        wm = context.window_manager
        self.timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
            
        return {'RUNNING_MODAL'}
        
    # Applies fcurve to bone property at specified keyframe
    def apply_fcurve(self, obj, fc, frame):
        data_path = fc.data_path 
        idx = fc.array_index # Specifies which component is being animated
        value = fc.evaluate(frame) # Calculates the interpolated val of an anim curve at frame

        # CASE 1: custom property on bone
        # For formatted bones like pose.bones["MSTR-Mouth"]["Tooth Visibility"]
        custom_match = re.match(r'(pose\.bones\[".+?"\])\["(.+?)"\]', data_path)

        if custom_match:
            # Save bone expression and prop name from string matched by re
            bone_expr = custom_match.group(1) # First parenthesized subgroup, ex: pose.bones["MSTR-Mouth"]
            prop_name = custom_match.group(2) # Second parenthesized subgroup, ex: Tooth Visibility

            # Get bone and its property
            bone = obj.path_resolve(bone_expr)
            val = bone[prop_name]
            
            # Skip properties that are non-numeric
            if not isinstance(val, float):
                return
            
            # Apply the fcurve to the bone property and insert keyframe
            bone[prop_name] = value
            bone.keyframe_insert(data_path=f'["{prop_name}"]', frame=frame)
            return

        # CASE 2: normal property
        # For formatted bones like pose.bones["DEF-Teeth_upp1.R"].location 
        owner_path, prop_name = data_path.rsplit(".", 1)
        
        # Get bone and its property
        owner = obj.path_resolve(owner_path)
        prop = getattr(owner, prop_name)

        # If property is a vector or quaternion and not a string
        if hasattr(prop, "__len__") and not isinstance(prop, str):
            # Apply the interpolated val to the property at inserted keyframe
            prop[idx] = value

            owner.keyframe_insert(
                data_path=prop_name,
                index=idx,
                frame=frame
            )
        else:
            # Set bone's prop name to interpolated val and insert keyframe
            owner[prop_name] = value

            owner.keyframe_insert(
                data_path=prop_name,
                frame=frame
            )
    
    # Inserts keyframes based on keyframe_data.json created by audio-to-viseme pipeline
    def insert_keyframes(self, context):
        settings = context.scene.auto_lip_sync
        armature = settings.target_rig
        
        temp_dir = Path(bpy.app.tempdir)
        keyframe_data_path = temp_dir / "keyframe_data.json"

        if not os.path.exists(keyframe_data_path):
            self.report({'ERROR'}, "Keyframe file not generated (subprocess failed)")
            return {'CANCELLED'}

        with open(keyframe_data_path, 'r') as f:
            keyframe_data_dict = json.load(f)

        viseme_lookup = {}
        for item in settings.viseme_mappings:
            viseme_lookup[item.viseme_name] = item.pose_asset

        for i, keyframe in enumerate(keyframe_data_dict["keyframes"]):
            viseme = keyframe["viseme"]
            pose_asset = viseme_lookup.get(viseme)

            if pose_asset is None:
                continue
            
            for slot in pose_asset.slots:
                channelbag = anim_utils.action_get_channelbag_for_slot(pose_asset, slot)
                for fc in channelbag.fcurves:
                    self.apply_fcurve(armature, fc, keyframe["start"])

                    # Insert two keyframes to hold sil visemes that aren't at the end
                    # One at the start frame and another at the end frame
                    if viseme == "sil" and i != len(keyframe_data_dict["keyframes"])-1:
                        self.apply_fcurve(armature, fc, keyframe["end"]-1)
                        
            # Update progress bar for every keyframe being inserted
            local = (i + 1) / len(keyframe_data_dict["keyframes"])
            settings.progress = settings.progress + local * 0.2
            for area in context.screen.areas:
                area.tag_redraw()
            
    # Clears existing keyframes within the rendered range for relevant bones
    # Used before insertion and only affects bone properties about to be keyframed
    def clear_keyframes(self, context):
        settings = context.scene.auto_lip_sync
        start = context.scene.frame_start
        end = context.scene.frame_end
        armature = settings.target_rig
        target_action = armature.animation_data.action

        affected_channels = set()

        # For each pose asset in the viseme mapping table
        for item in settings.viseme_mappings:
            pose_asset = item.pose_asset 

            if not pose_asset:
                continue

            # Collect channels affected by pose asset
            for slot in pose_asset.slots:
                channelbag = anim_utils.action_get_channelbag_for_slot(pose_asset, slot)
                for fc in channelbag.fcurves:
                    if fc.data_path.startswith("pose.bones["):
                        affected_channels.add(
                            (fc.data_path, fc.array_index)
                        )
    
        # Remove keys in render range
        for slot in target_action.slots:
            channelbag = anim_utils.action_get_channelbag_for_slot(target_action, slot)
            for fc in channelbag.fcurves:
                channel_id = (fc.data_path, fc.array_index)

                if channel_id not in affected_channels:
                    continue

                # Remove keys in frame range
                for kp in reversed(fc.keyframe_points):
                    frame = round(kp.co.x) # Frame number of specific keyframe

                    if start <= round(frame) <= end:
                        fc.keyframe_points.remove(kp)

                fc.update()

    
    # Periodically checks subprocess status and inserts keyframes when done
    def modal(self, context, event):    
        settings = context.scene.auto_lip_sync
        armature = settings.target_rig
        SUBPROCESS_WEIGHT = 0.7
        action_name = f"AutoLipSync_{armature.name}"
        
        # if event.type == 'TIMER':
        #     # If subprocess is still running    
        #     try:
        #         while True:
        #             line = self.queue.get_nowait()
        #             if line.startswith("PROGRESS"):
        #                 settings.progress = float(line.split()[1]) * SUBPROCESS_WEIGHT
        #                 for area in context.screen.areas:
        #                     area.tag_redraw()
        #     except queue.Empty:
        #         pass

        # Subprocess finished 
        if self.process.poll() is not None:
            if armature.animation_data is None:
                armature.animation_data_create()

            action = bpy.data.actions.get(action_name)

            # Create auto lip sync action for the target rig
            if action is None:
                action = bpy.data.actions.new(action_name)

            armature.animation_data.action = action

            # Clear existing keyframes if enabled
            if settings.clear_existing_keyframes:
                self.clear_keyframes(context)

            # Insert keyframes
            self.insert_keyframes(context)

            wm = context.window_manager
            wm.event_timer_remove(self.timer)

            settings.progress = 1.0
            for area in context.screen.areas:
                area.tag_redraw()
            
            settings.is_generating = False

            self.report(
                {'INFO'}, 
                f"Lip sync generated in Action '{action.name}'"
            )

            return {'FINISHED'}
        
        return {'RUNNING_MODAL'}