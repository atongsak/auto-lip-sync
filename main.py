import torch
import whisperx
import numpy as np
from phonemizer import phonemize
from phonemizer.backend.espeak.wrapper import EspeakWrapper
import pipeline_functions
from viseme_sets import SET_MAPPING_DICT
import json
import os

# REMOVE later when no longer printing stuff
import sys
sys.stdout.reconfigure(encoding='utf-8')


def main():
    settings_dict = {}
  
    # Get file path for settings.json
    if "--" in sys.argv:
        file_path = sys.argv[-1]
        print(file_path)
    
    # DELETE LATER
    # file_path = "C:\\Users\\SPIRO\\AppData\\Local\\Temp\\blender_a20852\\settings.json"

    # Load settings as dict
    with open(file_path, 'r') as f:
        settings_dict = json.load(f)

    # Initialize important lip sync variables
    viseme_set = settings_dict["viseme_set"]
    viseme_mapping = SET_MAPPING_DICT[viseme_set]
    audio_path = settings_dict["audio_path"]
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
    
    print(f"PROGRESS 0.1", flush=True)

    # Transcribe with original Whisper (batched)
    model = whisperx.load_model(settings_dict["model_size"], device, compute_type=compute_type, language="en")
    audio = whisperx.load_audio(audio_path)
    result = model.transcribe(audio, batch_size=batch_size)
    transcript = result["segments"]
    print(transcript) # before alignment

    # Use Phonemize to get the transcript in terms of phonemes
    phone_transcript = [{
        "text": phonemize(segment["text"]), 
        "start": segment["start"], 
        "end": segment["end"]
    } for segment in transcript]

    print(f"PROGRESS 0.3", flush=True)

    # Align Whisper output
    aligner_model = "facebook/wav2vec2-large-960h-lv60"
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device, model_name=aligner_model)
    result = whisperx.align(phone_transcript, model_a, metadata, audio, device, return_char_alignments=True)

    print(f"PROGRESS 0.5", flush=True)

    phoneme_timings = result["segments"][0].get('chars')[:-1]

    visemes = pipeline_functions.phonemes_to_visemes(
        phoneme_timings, 
        viseme_mapping, 
        settings_dict
    )

    print(f"PROGRESS 0.7", flush=True)

    viseme_data_path = os.path.join(parent_dir, f"visemes.json")
    with open(viseme_data_path, 'w', encoding='utf-8') as f:
        text = json.dumps(visemes, ensure_ascii=False, indent=4)
        f.write(text)

    cleaned = pipeline_functions.cleanup_visemes(
        visemes, 
        viseme_mapping,
        settings_dict
    )

    print(f"PROGRESS 0.9", flush=True)

    cleaned_data_path = os.path.join(parent_dir, f"keyframe_data.json")
    with open(cleaned_data_path, 'w', encoding='utf-8') as f:
        text = json.dumps(cleaned, ensure_ascii=False, indent=4)
        f.write(text)

    print(f"PROGRESS 1.0", flush=True)


if __name__ == "__main__":
    # Testing this fix for Windows
    EspeakWrapper.set_library(r"C:\Program Files\eSpeak NG\libespeak-ng.dll")

    main()