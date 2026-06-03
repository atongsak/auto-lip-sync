from ..core.constants import VISEME_SETS

# Returns dict of mapped visemes
def get_mapped_visemes(context):
    settings = context.scene.auto_lip_sync
    viseme_mappings = settings.viseme_mappings
    visemes = VISEME_SETS[settings.viseme_set]["visemes"]

    mapped_visemes_dict = {}

    for index, viseme in enumerate(viseme_mappings):
        mapped_visemes_dict[visemes[index]] = viseme.pose_asset.name
        
    return mapped_visemes_dict