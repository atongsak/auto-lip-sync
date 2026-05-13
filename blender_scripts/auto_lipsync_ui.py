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


def get_viseme_set_items(self, context):
    return [
        (key, value["label"], value["description"])
        for key, value in VISEME_SETS.items()
    ]
    
    
def initialize_visemes(scene):
    settings = scene.auto_lip_sync
    
    settings.viseme_mappings.clear()
    
    viseme_key = settings.viseme_set 
    visemes = VISEME_SETS[viseme_key]["visemes"]
    
    for viseme in visemes:
        item = settings.viseme_mappings.add()
        item.viseme_name = viseme


def update_viseme_set(self, context):
    initialize_visemes(context.scene)


def poll_pose_assets(self, action):
    return action.asset_data is not None


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


class VisemeItem(bpy.types.PropertyGroup):
    """Corresponding viseme name and pose asset dropdown"""
    viseme_name: bpy.props.StringProperty()

    pose_asset: bpy.props.PointerProperty(
        name="Pose Asset",
        type=bpy.types.Action,
        poll=poll_pose_assets
    )


class AutoLipSyncSettings(bpy.types.PropertyGroup):
    VISEME_SET_ITEMS = [
        ("MICROSOFT_22", "22 Visemes", "Microsoft's 22 viseme set"),
        ("META_15", "15 Visemes", "Meta's 15 viseme set"),
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
    
    target_channel: bpy.props.EnumProperty(
        name="",
        items=list_audio_channels
    )
    
    viseme_mappings: bpy.props.CollectionProperty(type=VisemeItem)
    
    mouth_close_delay: bpy.props.FloatProperty(
        name="Milliseconds",
        default=0.0,
        min=0.0,
        max=5000.0, # 5 secs
        description="How long silence should last before closing the mouth"
    )
    
    jaw_amp: bpy.props.FloatProperty(
        name="Amplitude",
        default=0.0,
        min=0.0,
        max=10.0, 
        description="Jaw amplification"
    )


class VisemeMappingSubPanel(bpy.types.Panel):
    """Viseme/mouth pose mapping subpanel"""
    bl_label = "Viseme Mapping"
    bl_idname = "VIEW3D_PT_viseme_subpanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_lip_sync" # Ties to main panel
    bl_options = {'DEFAULT_CLOSED'} # Enables the triangle
    
    @classmethod
    def poll(cls, context):
        # Only show viseme mapping if target rig is selected/True
        return context.scene.auto_lip_sync.target_rig
    
    def draw(self, context):
        layout = self.layout  
        settings = context.scene.auto_lip_sync
    
        header = layout.row()
        header.label(text="Viseme")
        header.label(text="Mouth Pose")
    
        for item in settings.viseme_mappings:
            row = layout.row()
            row.label(text=item.viseme_name)
            row.prop(item, "pose_asset", text="")
           
       
class AnimationSettingsSubPanel(bpy.types.Panel):
    """Animation settings subpanel"""
    bl_label = "Animation Settings"
    bl_idname = "VIEW3D_PT_animsettings_subpanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_lip_sync" # Ties to main panel
    bl_options = {'DEFAULT_CLOSED'} # Enables the triangle
    
    @classmethod
    def poll(cls, context):
        # Only show viseme mapping if target rig is selected/True
        return context.scene.auto_lip_sync.target_rig

    def draw(self, context):
        layout = self.layout
        
        close_header = layout.row()
        close_header.label(text="Close Mouth After:")
        layout.prop(context.scene.auto_lip_sync, "mouth_close_delay", slider=True)
        
        # TODO: Figure out how I'm going to amplify the jaw based on volume
        jaw_header = layout.row()
        jaw_header.label(text="Speech Intensity:")
        layout.prop(context.scene.auto_lip_sync, "jaw_amp", slider=True)



class GenerateKeyframesSubPanel(bpy.types.Panel):
    bl_label = "Generate Keyframes"
    bl_idname = "VIEW3D_PT_genframes_subpanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_lip_sync"
    bl_options = {'HIDE_HEADER'}
    
    @classmethod
    def poll(cls, context):
        # Only show viseme mapping if target rig is selected/True
        return context.scene.auto_lip_sync.target_rig
    
    def draw(self, context):
        layout = self.layout
        # TODO: Implement generate keyframes button
        layout.operator("object.shade_smooth", text="Generate keyframes")


class AutoLipSyncPanel(bpy.types.Panel):
    """Main add-on panel"""
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
    AutoLipSyncSettings,
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
    
    # TODO: May be risky if multiple scenes exist
    initialize_visemes(bpy.context.scene)

def unregister():
    del bpy.types.Scene.auto_lip_sync
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()