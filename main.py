import torch
import torchvision
import torchaudio
import whisperx
import numpy as np
from phonemizer import phonemize
from phonemizer.backend.espeak.wrapper import EspeakWrapper
import pipeline_functions
from viseme_sets import SET_MAPPING_DICT
import sys
import json
import os

# The way it should work is:
# Parse request.json to store data
# If there are multiple audio clips, loop through them to gen keyframes
# Take into account the start and end frames when adding keyframe data to the keyframe_data.json


# REMOVE later when no longer printing stuff
import sys

sys.stdout.reconfigure(encoding='utf-8')


def main():
    settings_dict = {}
    keyframe_data_dict = {}
    keyframe_data_visemes = []

    progress = 0.0
    
    # Whisper can handle <25 MB
    limit_bytes = 25 * 1024 * 1024

    # Get file path for settings.json
    if "--" in sys.argv:
        file_path = sys.argv[-1]
        print(file_path)
    
    # DELETE LATER
    file_path = "C:\\Users\\SPIRO\\AppData\\Local\\Temp\\blender_a41264\\settings.json"

    # Load settings as dict
    with open(file_path, 'r') as f:
        settings_dict = json.load(f)

    render_start = settings_dict["render_start"]
    render_end = settings_dict["render_end"]
    viseme_set = settings_dict["viseme_set"]
    viseme_mapping = SET_MAPPING_DICT[viseme_set]
    mouth_close_delay = settings_dict["mouth_close_delay"]
    audio_strips = settings_dict["audio"].get("strips")
    parent_dir = os.path.dirname(file_path)

    use_cuda_if_avail = True
    if use_cuda_if_avail and torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"

    if not hasattr(np, "NaN"):
        np.NaN = np.nan

    batch_size = 16 # reduce if low on GPU mem
    compute_type = "float16" if device == "gpu" else "int8" # change to "int8" if low on GPU mem (may reduce accuracy)

    progress = 0.1
    print(f"PROGRESS {progress}", flush=True)

    all_visemes = []

    for index, strip in enumerate(audio_strips):
        audio_file = strip.get("path")
        file_size = os.path.getsize(audio_file)

        # Skip audio strip if it exceeds 25 MB
        if file_size > limit_bytes:
            print(f"File is larger than 25MB ({file_size} bytes)")
            continue

        # Skip audio strip if outside the rendered portion
        if strip["end"] <= render_start or strip["start"] >= render_end:
            continue

        print(settings_dict["model_size"])

        # Transcribe with original whisper (batched)
        model = whisperx.load_model(settings_dict["model_size"], device, compute_type=compute_type, language="en")

        audio = whisperx.load_audio(audio_file)
        result = model.transcribe(audio, batch_size=batch_size)
        transcript = result["segments"]
        print(transcript) # before alignment

        # Use phonemize to get the transcript in terms of phonemes
        phone_transcript = [{
            "text": phonemize(segment["text"]), 
            "start": segment["start"], 
            "end": segment["end"]
        } for segment in transcript]

        # Align whisper output
        aligner_model = "facebook/wav2vec2-large-960h-lv60"
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device, model_name=aligner_model)
        result = whisperx.align(phone_transcript, model_a, metadata, audio, device, return_char_alignments=True)

        phoneme_timings = result["segments"][0].get('chars')[:-1]

        viseme_set = settings_dict["viseme_set"]

        visemes = pipeline_functions.phonemes_to_visemes(
            phoneme_timings, 
            viseme_mapping, 
            strip["start"], #/ settings_dict["fps"], 
            settings_dict
        )

        all_visemes.extend(visemes)

        # viseme_data_path = os.path.join(parent_dir, f"visemes{index}.json")
        # with open(viseme_data_path, 'w', encoding='utf-8') as f:
        #     text = json.dumps(visemes, ensure_ascii=False, indent=4)
        #     f.write(text)

    cleaned = pipeline_functions.cleanup_visemes(
        all_visemes, 
        viseme_mapping,
        render_end, 
        mouth_close_delay
    )

    for entry in cleaned:
        start_frame = entry["start"] - strip["offset"]
        end_frame = entry["end"] - strip["offset"]
        
        # Ignore visemes cut off by left trim
        if start_frame < strip["start"]:
            # print("ignore visemes cut off by left trim")
            continue
        
        # Ignore visemes cut off by right trim
        if start_frame >= strip["end"]:
            # print("ignore visemes cutoff by right trim")
            continue

        # If entry is not within the rendered range, skip
        if start_frame < render_start or start_frame >= render_end:
            continue    
        else:
            entry_values = entry.copy()
            entry_values["start_frame"] = start_frame
            entry_values["end_frame"] = end_frame
            keyframe_data_visemes.append(entry_values)

    total = len(audio_strips)
    progress += (index + 1) / total
    print(f"PROGRESS {progress}", flush=True)

    viseme_data_path = os.path.join(parent_dir, f"visemes.json")
    with open(viseme_data_path, 'w', encoding='utf-8') as f:
        text = json.dumps(all_visemes, ensure_ascii=False, indent=4)
        f.write(text)

    

    with open(viseme_data_path, 'w', encoding='utf-8') as f:
        text = json.dumps(cleaned, ensure_ascii=False, indent=4)
        f.write(text)

    keyframe_data_dict["keyframes"] = keyframe_data_visemes

    keyframe_data_path = os.path.join(parent_dir, "keyframe_data.json")
    with open(keyframe_data_path, 'w', encoding='utf-8') as f:
        text = json.dumps(keyframe_data_dict, ensure_ascii=False, indent=4)
        f.write(text)

if __name__ == "__main__":
    # Testing this fix for Windows
    EspeakWrapper.set_library(r"C:\Program Files\eSpeak NG\libespeak-ng.dll")

    main()