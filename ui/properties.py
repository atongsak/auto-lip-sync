import bpy
from bpy_extras import anim_utils
from ..core.constants import VISEME_SETS

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

    COMPUTE_OPTIONS = [
        ("CPU_COMPUTE", "CPU", "Run ASR model on CPU")
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
    
    compute: bpy.props.EnumProperty(
        name="",
        items=COMPUTE_OPTIONS,
        default="CPU_COMPUTE"
    )

    mouth_close_delay: bpy.props.FloatProperty(
        name="Frames",
        default=8.0,
        min=0.0,
        max=20, # 20 frames
        description="How many frames silence should last before closing the mouth"
    )
    
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


class SetupSettings(bpy.types.PropertyGroup):
    INSTALLATION_OPTIONS = [
        ("CPU_Install", "CPU Dependencies", "CPU Dependencies")
    ]

    installations: bpy.props.EnumProperty(
        name="",
        items=INSTALLATION_OPTIONS,
        default="CPU_Install"
    )

    cpu_installed: bpy.props.BoolProperty(
        name="CPU Installed",
        default=False
    )

    needs_refresh: bpy.props.BoolProperty(default=True)

    installing: bpy.props.BoolProperty(default=False)

    install_log: bpy.props.StringProperty(
        name="Install Status",
        default=""
    )