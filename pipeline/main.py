import torch
import whisperx
import numpy as np
from phonemizer import phonemize
import pipeline_functions
from viseme_sets import SET_MAPPING_DICT
import json
import os
import sys
import argparse

def init_espeak():
    import platform
    from pathlib import Path

    from phonemizer.backend.espeak.wrapper import EspeakWrapper

    addon_root = Path(__file__).parent.parent

    if platform.system() == "Windows":
        dll_path = addon_root / "bin" / "windows" / "libespeak-ng.dll"
        EspeakWrapper.set_library(str(dll_path))

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--file", required=True)
    parser.add_argument("--compute", default="CPU_COMPUTE")

    return parser.parse_known_args(sys.argv[sys.argv.index("--") + 1:])[0]

def main():
    settings_dict = {}
    args = parse_args()

    file_path = args.file
    compute_mode = args.compute

    print("ARGV:", sys.argv)
    print("PARSED FILE:", file_path)
  
    # Load settings as dict
    with open(file_path, 'r') as f:
        settings_dict = json.load(f)

    # Initialize important lip sync variables
    viseme_set = settings_dict["viseme_set"]
    viseme_mapping = SET_MAPPING_DICT[viseme_set]
    audio_path = settings_dict["audio_path"]
    parent_dir = os.path.dirname(file_path)

    device = "cuda" if (compute_mode == "GPU_COMPUTE" and torch.cuda.is_available()) else "cpu"

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

    print("ABOUT TO PHONEMIZE")
    for segment in transcript:
        print("TEXT:", segment["text"])
        print("PHONEME:", phonemize(segment["text"]))

    # Use Phonemize to get the transcript in terms of phonemes
    phone_transcript = [{
        "text": phonemize(segment["text"], backend="espeak", language="en-us"), 
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
    for p in phoneme_timings:
        print(p)

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
    init_espeak()
    main()