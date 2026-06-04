import bpy
from bpy.app.handlers import persistent
from .dependency_manager import refresh_dependency_state

@persistent
def initialize_viseme_data(dummy):
    for scene in bpy.data.scenes:
        settings = scene.auto_lip_sync

        if not settings.viseme_set_mappings:
            settings.init_viseme_set_mappings()
        
        if not settings.viseme_mappings:
            settings.rebuild_viseme_mappings()

@persistent
def refresh_on_load(dummy):
    for scene in bpy.data.scenes:
        refresh_dependency_state(scene)