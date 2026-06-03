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
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import bpy
from .ui.main_panel import AutoLipSyncPanel, VisemeMappingSubPanel, AnimationSettingsSubPanel, GenerateKeyframesSubPanel
from .ui.properties import VisemeItem, VisemeSetMappingGroup, AutoLipSyncSettings, SetupSettings
from .ui.setup_panel import SetupPanel
from .operators.audio_to_viseme import AudioToVisemeOperator
from .operators.install_dependencies import InstallDependenciesOperator
from .core.handlers import initialize_viseme_data
from .core.dependency_manager import refresh_dependency_state

EspeakWrapper = None

classes = (
    VisemeItem,
    VisemeSetMappingGroup,
    AutoLipSyncSettings,
    SetupSettings,

    AudioToVisemeOperator,
    InstallDependenciesOperator,
    
    SetupPanel,
    AutoLipSyncPanel,
    VisemeMappingSubPanel,
    AnimationSettingsSubPanel,
    GenerateKeyframesSubPanel
)

def delayed_refresh():
    if not bpy.data.scenes:
        return 1.0  # retry later

    scene = bpy.context.scene if bpy.context else None
    if not scene:
        return 1.0

    refresh_dependency_state(scene)

    return None  # stop timer

def register():
    for cls in classes: 
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            pass

    bpy.types.Scene.setup = bpy.props.PointerProperty(
        type=SetupSettings
    )

    bpy.types.Scene.auto_lip_sync = bpy.props.PointerProperty(
        type=AutoLipSyncSettings
    )

    if initialize_viseme_data not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(
            initialize_viseme_data
        )

    bpy.app.timers.register(
        delayed_refresh,
        first_interval=3.0
    )
        
def unregister():
    if initialize_viseme_data in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(
            initialize_viseme_data
        )

    del bpy.types.Scene.setup
    del bpy.types.Scene.auto_lip_sync

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)