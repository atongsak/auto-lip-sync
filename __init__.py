'''
Copyright (C) 2026 Annette Tongsak
annettetongsak@gmail.com

Created by Annette Tongsak

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

import bpy
from .ui.main_panel import AutoLipSyncPanel, VisemeMappingSubPanel, AnimationSettingsSubPanel, GenerateKeyframesSubPanel
from .ui.properties import VisemeItem, VisemeSetMappingGroup, AutoLipSyncSettings, SetupSettings
from .ui.setup_panel import SetupPanel
from .ui.transcript_panel import TranscriptPanel
from .operators.audio_to_viseme import AudioToVisemeOperator
from .core.handlers import initialize_viseme_data, refresh_on_load
from .core.dependency_manager import refresh_dependency_state

EspeakWrapper = None

classes = (
    VisemeItem,
    VisemeSetMappingGroup,
    AutoLipSyncSettings,
    SetupSettings,

    AudioToVisemeOperator,
    
    SetupPanel,
    AutoLipSyncPanel,
    VisemeMappingSubPanel,
    AnimationSettingsSubPanel,
    GenerateKeyframesSubPanel,
    TranscriptPanel
)

registered_classes = []

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            registered_classes.append(cls)
        except Exception as e:
            print(f"Failed to register {cls.__name__}: {e}")

    # Global properties
    bpy.types.WindowManager.setup = bpy.props.PointerProperty(
        type=SetupSettings
    )

    # Scene-specific properties
    bpy.types.Scene.auto_lip_sync = bpy.props.PointerProperty(
        type=AutoLipSyncSettings
    )

    if initialize_viseme_data not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(
            initialize_viseme_data
        )

    if refresh_on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(
            refresh_on_load
        )

    if not bpy.app.timers.is_registered(refresh_dependency_state):
        bpy.app.timers.register(
            refresh_dependency_state,
            first_interval=0.5
        )

def unregister():
    # Unregister timers
    if bpy.app.timers.is_registered(refresh_dependency_state):
        bpy.app.timers.unregister(refresh_dependency_state)

    # Remove handlers
    if refresh_on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(
            refresh_on_load
        )

    if initialize_viseme_data in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(
            initialize_viseme_data
        )

    # Delete PointerProperties before unregistering classes
    if hasattr(bpy.types.WindowManager, "setup"):
        del bpy.types.WindowManager.setup

    if hasattr(bpy.types.Scene, "auto_lip_sync"):
        del bpy.types.Scene.auto_lip_sync

    # Unregister classes in reverse order
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(f"Failed to unregister {cls.__name__}: {e}")

    registered_classes.clear()