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

class AudioToVisemeOperator(bpy.types.Operator): 
    bl_idname = "auto_lip_sync.generate"
    bl_label = "Function that runs the audio-to-viseme process"   
    bl_description = "Generate and insert lip sync keyframes into the target action"  
            
    # Writes settings.json, starts subprocess, starts timer/modal loop
    def execute(self, context):
        settings = context.scene.auto_lip_sync
        settings.is_generating = True
        settings.progress = 0.0
        self.status = None
        
        mapped_visemes_dict = get_mapped_visemes(context)
        target_audio_path = get_target_audio_path(context)
       
        # Check file size of target channel audio wav
        file_size = os.path.getsize(target_audio_path)
        limit_bytes = 25 * 1024 * 1024 # Whisper can handle files <25 MB
        
        if file_size > limit_bytes:
            settings.is_generating = False
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

        # Save user preferences to settings.json
        temp_dir = Path(bpy.app.tempdir)
        settings_path = temp_dir / "settings.json"
        with open(settings_path, 'w', encoding='utf-8') as f:
            text = json.dumps(settings_dict, indent=4)
            f.write(text)

        addon_root = Path(__file__).parent.parent
        pipeline_script = addon_root / "pipeline" / "main.py"

        print(addon_root)

        # Find Blender's extension-local Python packages
        extension_pkg = Path.home() / (
            "Library/Application Support/Blender/5.1/extensions/.local/lib/python3.13/site-packages"
        )

        print("EXTENSION PACKAGES:", extension_pkg)
        print("EXISTS:", extension_pkg.exists())

        env = os.environ.copy()
        env["PYTHONPATH"] = str(extension_pkg)
        
        # Execute audio-to-keyframes pipeline
        command = [sys.executable, "-u", "-Xutf8", str(pipeline_script), "--", "--file", str(settings_path), "--compute", settings.compute]

        self.process = subprocess.Popen(
            command,
            # stdout = subprocess.PIPE, # Save command's output into var instead of printing
            # stderr = subprocess.STDOUT,
            env=env,
            text = True,
            bufsize = 1
        )
        
        # self.queue = queue.Queue()
                        
        # def enqueue_output(pipe, q):
        #     for line in iter(pipe.readline, ''):
        #         q.put(line)
        #     pipe.close()
            
        # # Create thread to read progress logs from main.py
        # self.thread = threading.Thread(
        #     target=enqueue_output,
        #     args=(self.process.stdout, self.queue),
        #     daemon=True
        # )
        # self.thread.start()
                    
        wm = context.window_manager
        self.timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        self.text = []
        settings.detected_transcript = ""
        self.inserting_keyframes = False

        # Initialize target action
        if settings.action_pref == "open_action":
            settings.target_action = context.object.animation_data.action.name
            
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
            bone_prop = bone[prop_name]
            
            # Skip properties that are non-numeric
            if not isinstance(bone_prop, float):
                return
            
            # Apply the fcurve to the bone property and insert keyframe
            bone_prop = value
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
         
    # Applies pose asset at specified keyframe
    def insert_one_keyframe(self, context, i):
        settings = context.scene.auto_lip_sync
        armature = settings.target_rig

        # Find the corresponding pose asset to a detected viseme
        keyframe = self.keyframes[i]
        viseme = keyframe["viseme"]
        pose_asset = self.viseme_lookup.get(viseme)

        # Skip if missing pose asset
        if pose_asset is None:
            return
        
        # Shift keyframes by -4.2f to account for anatomical accuracy
        keyframe["start"] -= 4.2
        keyframe["end"] -= 4.2
        
        # Apply pose asset to current keyframe
        for slot in pose_asset.slots:
            channelbag = anim_utils.action_get_channelbag_for_slot(pose_asset, slot)
            for fc in channelbag.fcurves:
                self.apply_fcurve(armature, fc, keyframe["start"])

                # Insert two keyframes to hold sil visemes that aren't at the end
                # One at the start frame and another at the end frame
                if viseme == "sil" and i != self.last_keyframe_index:
                    self.apply_fcurve(armature, fc, keyframe["end"]-1)

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
        wm = context.window_manager
        SUBPROCESS_WEIGHT = 0.5
        BATCH_SIZE = 40

        # Cancel the operator if user presses ESC or right mouse
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            wm.event_timer_remove(self.timer)
            settings.is_generating = False
            self.report(
                {'WARNING'},
                "Auto lip sync operation cancelled."
            )
            return {'CANCELLED'}

        # STEP 1: If subprocess is still running    
        # if event.type == 'TIMER':
        #     try:
        #         # Keep consuming and processing print messages in queue until empty
        #         while True:
        #             line = self.queue.get_nowait()
        #             if line.startswith("PROGRESS"):
        #                 settings.progress = float(line.split()[1]) * SUBPROCESS_WEIGHT
        #                 for area in context.screen.areas:
        #                     area.tag_redraw()
        #             elif line.startswith("MESSAGE"):
        #                 settings.progress_message = line.removeprefix("MESSAGE:").strip()
        #             elif line.startswith("STATUS"):
        #                 self.status = line.removeprefix("STATUS:").strip()
        #                 print(f"STATUS SET TO: {repr(self.status)}")
        #             elif line.startswith("TEXT"):
        #                 self.text.append(line.removeprefix("TEXT:").strip())
        #                 print(line.strip())
        #     except queue.Empty:
        #         pass
            
        # STEP 2: Once the subprocess is finished
        if self.process.poll() is not None and not self.inserting_keyframes: 
            if self.status == "NO_WORDS":
                wm.event_timer_remove(self.timer)
                settings.is_generating = False
                self.report(
                    {'WARNING'},
                    "No words were detected in the selected audio channel."
                )
                return {'CANCELLED'}

            if armature.animation_data is None:
                armature.animation_data_create()

            # Get action to insert keyframes in
            self.action = bpy.data.actions.get(settings.target_action)
            # Create a new action if it doesn't exist
            # TODO: Allow user to do this
            if self.action is None:
                self.action = bpy.data.actions.new(f"AutoLipSync_{armature.name}")
            armature.animation_data.action = self.action

            # Clear existing keyframes if enabled
            if settings.clear_existing_keyframes:
                self.clear_keyframes(context)

            temp_dir = Path(bpy.app.tempdir)
            keyframe_data_path = temp_dir / "keyframe_data.json"
            print(keyframe_data_path)

            if not os.path.exists(keyframe_data_path):
                settings.is_generating = False
                self.report({'ERROR'}, "Keyframe file not generated (subprocess failed)")
                return {'CANCELLED'}

            # Load keyframe_data.json to keyframe data dictionary
            with open(keyframe_data_path, 'r') as f:
                keyframe_data_dict = json.load(f)

            # Create dictionary of viseme-pose asset mappings
            self.viseme_lookup = {}
            for item in settings.viseme_mappings:
                self.viseme_lookup[item.viseme_name] = item.pose_asset

            # Initialize instance variables 
            self.keyframes = keyframe_data_dict["keyframes"]
            self.num_keyframes = len(self.keyframes)
            self.last_keyframe_index = self.num_keyframes-1

            self.inserting_keyframes = True
            self.current_keyframe = 0

            return {'RUNNING_MODAL'}

        # STEP 3: Insert keyframes in batches based on keyframe_data.json
        if self.inserting_keyframes:
            settings.progress_message = "Inserting keyframes..."

            for _ in range(BATCH_SIZE):
                if self.current_keyframe >= self.num_keyframes:
                    break
 
                self.insert_one_keyframe(context, self.current_keyframe)
                self.current_keyframe += 1

            settings.progress = SUBPROCESS_WEIGHT + self.current_keyframe / self.num_keyframes * (1.0 - SUBPROCESS_WEIGHT)

            for area in context.screen.areas:
                area.tag_redraw()

            # Continue inserting keyframes if not at the end
            if self.current_keyframe < self.num_keyframes:
                return {'RUNNING_MODAL'}

            settings.progress = 1.0
            for area in context.screen.areas:
                area.tag_redraw()
            
            wm.event_timer_remove(self.timer)
            settings.is_generating = False
            settings.progress_message = "Initializing variables..."

            self.report(
                {'INFO'}, 
                f"Lip sync generated in Action '{self.action.name}'"
            )

            settings.detected_transcript = " ".join(self.text)

            return {'FINISHED'}
        
        return {'RUNNING_MODAL'}