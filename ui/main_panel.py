import bpy

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
        venv_picker.prop(settings, "compute")
        
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
        
        if settings.viseme_mappings_valid():
            if settings.is_generating:
                layout.prop(settings, "progress", text="Running Auto Lip Sync...", slider=False)

            layout.operator("wm.run_subprocess", text="Generate keyframes")
            
        else:
            alert_row = layout.row()
            alert_row.label(text="Resolve viseme mapping errors to generate keyframes", icon='INFO')
