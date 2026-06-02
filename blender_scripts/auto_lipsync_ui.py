# TODO: Legacy info format - need to adjust for toml
bl_info = {
    "name": "Auto Lip Sync",
    "author": "Annette Tongsak",
    "version": (0, 0, 1),
    "blender": (5, 0, 1),
    "location": "3D Viewport > Sidebar > Auto Lip Sync",
    "description": "A Blender add-on that generates lip sync animation keyframes from audio and mouth poses",
    "category": "3D View",
}

import bpy
from bpy_extras import anim_utils
from bpy.app.handlers import persistent
import subprocess
import json
import os
import re
import queue
import threading


# TODO: Have these virtual environments be created for the user via subprocess operator
VENVS = {
    "CPU_PYTHON": "C:/Users/SPIRO/Documents/auto-lip-sync/.venv/Scripts/python.exe",
    "GPU_PYTHON": "C:/Users/SPIRO/Documents/auto-lip-sync/.venv_gpu/Scripts/python.exe"
}

# Path to external script
script_path = "C:/Users/SPIRO/Documents/auto-lip-sync/main.py"

VISEME_SETS = {
    "MICROSOFT_22": {
        "label": "22 Visemes",
        "description": "Microsoft's 22 viseme set",
        "visemes": [
            "sil", "a", "ah", "aw", "eh",
            "er", "ee", "oo", "oh", "ow",
            "oy", "ai", "h", "r", "l",
            "s", "sh", "th", "f, v", "t, d, n",
            "k, g", "b, m, p"
        ]
    },
    "META_15": {
        "label": "15 Visemes",
        "description": "Meta's 15 viseme set",
        "visemes": [
            "sil", "PP", "FF", "TH", "DD",
            "kk", "CH", "SS", "nn", "RR",
            "aa", "E", "I", "O", "U"
        ]
    }
}
    

@persistent
def initialize_viseme_data(dummy):
    for scene in bpy.data.scenes:
        settings = scene.auto_lip_sync

        if not settings.viseme_set_mappings:
            settings.init_viseme_set_mappings()
        
        if not settings.viseme_mappings:
            settings.rebuild_viseme_mappings()

bpy.app.handlers.load_post.append(initialize_viseme_data)


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


# Returns dict of mapped visemes
def get_mapped_visemes(context):
    settings = context.scene.auto_lip_sync
    viseme_mappings = settings.viseme_mappings
    visemes = VISEME_SETS[settings.viseme_set]["visemes"]

    mapped_visemes_dict = {}

    for index, viseme in enumerate(viseme_mappings):
        mapped_visemes_dict[visemes[index]] = viseme.pose_asset.name
        
    return mapped_visemes_dict
    
    
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
        
        print(bpy.app.tempdir)

        file_path = os.path.join(bpy.app.tempdir, "settings.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            text = json.dumps(settings_dict, indent=4)
            f.write(text)

        venv_path = VENVS[settings.venv]
        command = [venv_path, "-u", script_path, "--", file_path] 

        self.process = subprocess.Popen(
                        command,
                        #stdout = subprocess.PIPE, # Save command's output into var instead of printing
                        #stderr = subprocess.STDOUT,
                        #text = True
                    )
        
        self.queue = queue.Queue()
                        
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
        keyframe_data_path = os.path.join(bpy.app.tempdir, "keyframe_data.json")
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
    

class VisemeItem(bpy.types.PropertyGroup):
    # Returns pose assets to propagate dropdown
    def poll_pose_assets(self, action):
        return action.asset_data is not None

    viseme_name: bpy.props.StringProperty()

    pose_asset: bpy.props.PointerProperty(
        name="Pose Asset",
        type=bpy.types.Action,
        poll=poll_pose_assets
    )


class VisemeSetMappingGroup(bpy.types.PropertyGroup):
    viseme_set: bpy.props.StringProperty()

    viseme_mappings: bpy.props.CollectionProperty(type=VisemeItem)


class AutoLipSyncSettings(bpy.types.PropertyGroup):
    # Gets specified set's VisemeSetMapping Group
    def get_mapping_group(self, viseme_set):
        for group in self.viseme_set_mappings:
            if group.viseme_set == viseme_set:
                return group

    # Initializes VisemeItem with viseme_name in a collection
    def init_set_visemes(self, collection, viseme_set):
        for viseme in VISEME_SETS[viseme_set]["visemes"]:
            item = collection.add()
            item.viseme_name = viseme

    # Initializes VisemeSetMappingGroup
    def init_viseme_set_mappings(self):
        if not self.get_mapping_group("MICROSOFT_22"):
            microsoft_22 = self.viseme_set_mappings.add()
            microsoft_22.viseme_set = "MICROSOFT_22"
            self.init_set_visemes(microsoft_22.viseme_mappings, microsoft_22.viseme_set)
        
        if not self.get_mapping_group("META_15"):
            meta_15 = self.viseme_set_mappings.add()
            meta_15.viseme_set = "META_15"
            self.init_set_visemes(meta_15.viseme_mappings, meta_15.viseme_set)

    # Rebuilds self.viseme_mappings
    def rebuild_viseme_mappings(self):
        viseme_set_group = self.get_mapping_group(self.viseme_set)

        self.viseme_mappings.clear()

        visemes = viseme_set_group.viseme_mappings

        for viseme in visemes:
            item = self.viseme_mappings.add()
            item.viseme_name = viseme.viseme_name
            item.pose_asset = viseme.pose_asset

    # Store previous viseme set's mappings into cache
    def sync_set_visemes(self, source, target):
        # Save self.viseme_mappings to collection.viseme_mappings
        for src, dst in zip(source, target):
            dst.pose_asset = src.pose_asset
          
    # Saves viseme set's mappings to VisemeSetMappingGroup
    def cache_viseme_mappings(self):
        # Get the group corresponding to the current UI state
        viseme_set_group = self.get_mapping_group(self.prev_viseme_set)
        self.sync_set_visemes(self.viseme_mappings, viseme_set_group.viseme_mappings)

    # Updates stored viseme set
    def update_viseme_set(self, context):
        viseme_set_group = self.get_mapping_group(self.prev_viseme_set)
        
        # Save existing mapping to cache
        self.cache_viseme_mappings()
        
        # Clear active UI mappings
        self.viseme_mappings.clear()
        
        # If group empty, create defaults
        if not viseme_set_group:
            self.init_viseme_set_mappings()
        else: 
            self.rebuild_viseme_mappings()

        # Update prev_viseme_set
        self.prev_viseme_set = self.viseme_set

    # Returns list of audio channels to propagate dropdown
    def list_audio_channels(self, context):
        scene = context.scene
        items = [] 
        
        if scene.sequence_editor:
            channels = set()
            
            for strip in scene.sequence_editor.strips_all:
                if strip.type == 'SOUND':
                    channels.add(strip.channel)
            
            for channel in sorted(channels):
                items.append(
                    (str(channel),
                    f"Channel {channel}",
                    f"Audio channel {channel}")
                )
                    
        return items or [("None", "No audio", "No sound strips found")]

    # Valid/invalid state of viseme mappings
    def viseme_mappings_valid(self):
        validation = self.validate_viseme_mappings()
    
        return not any(validation.values())
    
    # Checks for problems among viseme mappings
    def validate_viseme_mappings(self):
        results = {
            "missing_action": [],
            "no_pose_animation": [],
            "missing_bones": []
        }

        rig = self.target_rig

        if rig is None or rig.type != 'ARMATURE':
            return results

        for viseme in self.viseme_mappings:
            action = viseme.pose_asset
            valid, reason = self.action_matches_rig(action, rig)

            if valid:
                continue

            results[reason].append(viseme.viseme_name)

        return results
    
    # Checks if action bones exist in rig bones
    def action_matches_rig(self, action, rig):
        rig_bones = set(rig.pose.bones.keys())
        action_bones = set()

        if action is None:
            return False, "missing_action"

        if not action.slots:
            return False, "no_pose_animation"

        for slot in action.slots:
            channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)

            if channelbag is None:
                continue

            for fc in channelbag.fcurves:

                path = fc.data_path

                if path.startswith('pose.bones["'):
                    bone_name = path.split('"')[1]
                    action_bones.add(bone_name)

        if not action_bones:
            return False, "no_pose_animation"

        missing = action_bones - rig_bones

        if missing:
            return False, "missing_bones"

        return True, None
        
    VISEME_SET_ITEMS = [
        ("MICROSOFT_22", "22 Visemes", "Microsoft's 22 viseme set"),
        ("META_15", "15 Visemes", "Meta's 15 viseme set"),
    ]
    
    MODEL_SIZES = [
        ("tiny", "tiny.en", "~10x relative speed"),
        ("base", "base.en", "~7x relative speed"),
        ("small", "small.en", "~4x relative speed"),
        ("medium", "medium.en", "~2x relative speed"),
        ("large", "large", "1x relative speed"),
        ("large-v2", "large-v2", "1x relative speed, improved accuracy over large"),
        ("turbo", "turbo", "~8x relative speed"),
    ]

    VENV_OPTIONS = [
        ("CPU_PYTHON", "CPU", "Run ASR model on CPU"),
        ("GPU_PYTHON", "GPU", "Run ASR model on GPU")
    ]
    
    target_rig: bpy.props.PointerProperty(
        name="",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'ARMATURE'
    )
    
    viseme_set: bpy.props.EnumProperty(
        name="",
        items=VISEME_SET_ITEMS,
        default="MICROSOFT_22",
        update=update_viseme_set
    )

    prev_viseme_set: bpy.props.StringProperty(
        default="MICROSOFT_22"
    )
    
    target_channel: bpy.props.EnumProperty(
        name="",
        items=list_audio_channels
    )
    
    # Active UI working set
    viseme_mappings: bpy.props.CollectionProperty(type=VisemeItem)

    # Persistent storage for each viseme set
    viseme_set_mappings: bpy.props.CollectionProperty(type=VisemeSetMappingGroup)
    
    clear_existing_keyframes: bpy.props.BoolProperty(
        name="",
        description="Clear existing and relevant keyframes in the Dope Sheet before insertion of lip sync keyframes",
        default=False
    )

    model_size: bpy.props.EnumProperty(
        name="",
        items=MODEL_SIZES,
        default="tiny"
    )

    venv: bpy.props.EnumProperty(
        name="",
        items=VENV_OPTIONS,
        default="CPU_PYTHON"
    )
    
    mouth_close_delay: bpy.props.FloatProperty(
        name="Frames",
        default=8.0,
        min=0.0,
        max=20, # 20 frames
        description="How many frames silence should last before closing the mouth"
    )
    
    # jaw_amp: bpy.props.FloatProperty(
    #     name="Amplitude",
    #     default=0.0,
    #     min=0.0,
    #     max=10.0, 
    #     description="Jaw amplification"
    # )

    progress: bpy.props.FloatProperty(
        name="Progress",
        subtype='FACTOR',
        default=0.0,
        min=0.0,
        max=1.0
    )
    
    is_generating: bpy.props.BoolProperty(
        default=False
    )


class VisemeMappingSubPanel(bpy.types.Panel):
    bl_label = "Viseme Mapping"
    bl_idname = "VIEW3D_PT_viseme_subpanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_lip_sync" 
    bl_options = {'DEFAULT_CLOSED'} 
    
    @classmethod
    def poll(cls, context):
        return context.scene.auto_lip_sync.target_rig
    
    def draw(self, context):
        layout = self.layout  
        settings = context.scene.auto_lip_sync
        
        validation = settings.validate_viseme_mappings()
        
        if validation["missing_action"]:
            box = layout.box()
            box.label(
                text=f"{len(validation['missing_action'])} visemes have no pose asset assigned",
                icon='ERROR'
            )
            box.label(
                text=", ".join(validation["missing_action"])
            )

        if validation["no_pose_animation"]:
            box = layout.box()
            box.label(
                text=f"{len(validation['no_pose_animation'])} visemes contain no pose bone animation",
                icon='ERROR'
            )
            box.label(
                text=", ".join(validation["no_pose_animation"])
            )

        if validation["missing_bones"]:
            box = layout.box()
            box.label(
                text=f"{len(validation['missing_bones'])} viseme mappings don't match the target rig",
                icon='ERROR'
            )
            box.label(
                text=", ".join(validation["missing_bones"])
            )
    
        header = layout.row()
        header.label(text="Viseme")
        header.label(text="Mouth Pose")
    
        for item in settings.viseme_mappings:
            row = layout.row()
            row.label(text=item.viseme_name)
            row.prop(item, "pose_asset", text="")
            
        
class AnimationSettingsSubPanel(bpy.types.Panel):
    bl_label = "Animation Settings"
    bl_idname = "VIEW3D_PT_animsettings_subpanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_lip_sync" 
    bl_options = {'DEFAULT_CLOSED'} 
    
    @classmethod
    def poll(cls, context):
        settings = context.scene.auto_lip_sync
        return settings.target_rig
    
    def draw(self, context):
        settings = context.scene.auto_lip_sync
        layout = self.layout
        
        model_picker = layout.row()
        model_picker.label(text="ASR Model Size")
        model_picker.prop(settings, "model_size")

        venv_picker = layout.row()
        venv_picker.label(text="Compute")
        venv_picker.prop(settings, "venv")
        
        clear_existing_toggle = layout.row()
        clear_existing_toggle.label(text="Clear existing keyframes")
        clear_existing_toggle.prop(settings, "clear_existing_keyframes")

        close_header = layout.row()
        close_header.label(text="Close Mouth After:")
        layout.prop(settings, "mouth_close_delay", slider=True)
        
        # TODO: Figure out how I'm going to amplify the jaw based on volume
        # jaw_header = layout.row()
        # jaw_header.label(text="Speech Intensity:")
        # layout.prop(settings, "jaw_amp", slider=True)
        

class GenerateKeyframesSubPanel(bpy.types.Panel):
    bl_label = "Generate Keyframes"
    bl_idname = "VIEW3D_PT_genframes_subpanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_lip_sync"
    bl_options = {'HIDE_HEADER'}
    
    @classmethod
    def poll(cls, context):
        return context.scene.auto_lip_sync.target_rig 
            
    def draw(self, context):
        layout = self.layout
        settings = context.scene.auto_lip_sync
        
        if settings.viseme_mappings_valid():
            if settings.is_generating:
                layout.prop(settings, "progress", text="Running Auto Lip Sync...", slider=False)

            layout.operator("wm.run_subprocess", text="Generate keyframes")
            
        else:
            alert_row = layout.row()
            alert_row.label(text="Resolve viseme mapping errors to generate keyframes", icon='INFO')

   
class AutoLipSyncPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_lip_sync"
    bl_category = "Auto Lip Sync"
    bl_label = "Auto Lip Sync"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    def draw(self, context):
        settings = context.scene.auto_lip_sync
        layout = self.layout
        
        rig_row = layout.row()
        rig_row.label(text="Target Rig")
        rig_row.prop(settings, "target_rig")
        
        set_row = layout.row()
        set_row.label(text="Viseme Set")
        set_row.prop(settings, "viseme_set")
        
        channel_row = layout.row()
        channel_row.label(text="Audio Channel")
        channel_row.prop(settings, "target_channel")

        if settings.target_rig == None:
            alert_row = layout.row()
            alert_row.label(text="Select a target rig to start", icon='INFO')

        
classes = (
    VisemeItem,
    VisemeSetMappingGroup,
    AutoLipSyncSettings,
    AudioToVisemeOperator,
    AutoLipSyncPanel,
    VisemeMappingSubPanel,
    AnimationSettingsSubPanel,
    GenerateKeyframesSubPanel
)


def register():
    for cls in classes: bpy.utils.register_class(cls)
    
    bpy.types.Scene.auto_lip_sync = bpy.props.PointerProperty(
        type=AutoLipSyncSettings
    )

    initialize_viseme_data(None)
        

def unregister():
    del bpy.types.Scene.auto_lip_sync

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()