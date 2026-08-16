import bpy
from ..operators.audio_to_viseme import AudioToVisemeOperator

class AutoLipSyncPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_lip_sync"
    bl_category = "Auto Lip Sync"
    bl_label = "Auto Lip Sync"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    def draw(self, context):
        settings = context.scene.auto_lip_sync
        layout = self.layout

        # Alert if no target channel
        if settings.target_channel == "None" or settings.target_channel == "":
            box = layout.box()
            box.label(
                text="No unmuted audio channel selected",
                icon='ERROR'
            )

        # Alert if no target action
        invalid_choose_action = (settings.target_action == ("None" or "") and settings.action_pref == "choose_action")
        invalid_open_action = (not bpy.data.actions and settings.action_pref == "open_action")
        if invalid_choose_action or invalid_open_action:
            box = layout.box()
            box.label(
                text="No target action selected" if settings.action_pref == "choose_action" else "No actions exist", 
                icon='ERROR'
            )

        rig_row = layout.row()
        rig_row.label(text="Target Rig")
        rig_row.prop(settings, "target_rig")
        
        set_row = layout.row()
        set_row.label(text="Viseme Set")
        set_row.prop(settings, "viseme_set")
        
        channel_row = layout.row()
        channel_row.label(text="Audio Channel")
        channel_row.prop(settings, "target_channel")

        action_row = layout.row()
        action_row.label(text="Insert Keyframes Into")
        action_row.prop(settings, "action_pref")

        # Provide dropdown if user wants to choose action
        if settings.action_pref == "choose_action":
            action_dropdown_row = layout.row()
            action_dropdown_row.label(text="Target Action")
            action_dropdown_row.prop(settings, "target_action")           

        # Alert if no target rig 
        if settings.target_rig is None:
            alert_row = layout.row()
            alert_row.label(text="Select a target rig to start", icon='INFO')
        
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
        return context.scene.auto_lip_sync.target_rig
    
    def draw(self, context):
        settings = context.scene.auto_lip_sync
        layout = self.layout
        
        model_picker = layout.row()
        model_picker.label(text="ASR Model Size")
        model_picker.prop(settings, "model_size")

        # compute_picker = layout.row()
        # compute_picker.label(text="Compute")
        # compute_picker.prop(settings, "compute")
        
        clear_existing_toggle = layout.row()
        clear_existing_toggle.label(text="Clear existing keyframes")
        clear_existing_toggle.prop(settings, "clear_existing_keyframes")

        close_header = layout.row()
        close_header.label(text="Close Mouth After:")
        layout.prop(settings, "mouth_close_delay", slider=True)

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
                
        valid_target_action = True
        invalid_choose_action = (settings.target_action == ("None" or "") and settings.action_pref == "choose_action")
        invalid_open_action = (not bpy.data.actions and settings.action_pref == "open_action")
        if invalid_choose_action or invalid_open_action:
            valid_target_action = False

        if settings.viseme_mappings_valid() and settings.target_channel != "None" and settings.target_channel != "" and valid_target_action:
            if settings.is_generating:
                layout.prop(settings, "progress", text=settings.progress_message, slider=False)
                
            layout.operator(AudioToVisemeOperator.bl_idname, text="Generate keyframes")
            
        else:
            alert_row = layout.row()
            alert_row.label(text="Resolve errors to generate keyframes", icon='INFO')