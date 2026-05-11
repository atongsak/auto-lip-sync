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
    
    viseme_key = "MICROSOFT_22"
    visemes = VISEME_SETS[viseme_key]["visemes"]
    
    for viseme in visemes:
        item = settings.viseme_mappings.add()
        item.viseme_name = viseme

def update_viseme_set(self, context):
    initialize_visemes(context.scene)

def list_pose_assets(self, context):
    """Returns a list of items in the user's asset library"""
    # TODO: Only show the assets that are associated with the selected model for lip sync
    items = [("None", "None", "None")]
    for action in bpy.data.actions:
        if action.asset_data:
            items.append((action.name, action.name, f"{action.name}"))
    return items

class VisemeItem(bpy.types.PropertyGroup):
    """Corresponding viseme name and pose asset dropdown"""
    viseme_name: bpy.props.StringProperty()
    
    # Dropdown enum
    pose_asset: bpy.props.EnumProperty(
        name="Pose Asset",
        items=list_pose_assets
    )

class AutoLipSyncSettings(bpy.types.PropertyGroup):
    VISEME_SET_ITEMS = [
        ("MICROSOFT_22", "22 Visemes", "Microsoft's 22 viseme set"),
        ("META_15", "15 Visemes", "Meta's 15 viseme set"),
    ]
    
    viseme_set: bpy.props.EnumProperty(
        name="",
        items=VISEME_SET_ITEMS,
        default="MICROSOFT_22",
        update=update_viseme_set
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
    
    def draw(self, context):
        layout = self.layout  
        tool = context.scene.auto_lip_sync
        
        header = layout.row()
        header.label(text="Viseme")
        header.label(text="Mouth Pose")
    
        for item in tool.viseme_mappings:
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
        scene = context.scene
        
        row = layout.row()
        row.label(text="Viseme Set")
        row.prop(settings, "viseme_set")


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