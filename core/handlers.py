import bpy
from bpy.app.handlers import persistent

@persistent
def initialize_viseme_data(dummy):
    for scene in bpy.data.scenes:
        settings = scene.auto_lip_sync

        if not settings.viseme_set_mappings:
            settings.init_viseme_set_mappings()
        
        if not settings.viseme_mappings:
            settings.rebuild_viseme_mappings()