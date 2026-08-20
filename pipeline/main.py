# import torch
import warnings

warnings.filterwarnings(
    "ignore",
    message=r"\s*torchcodec is not installed correctly.*",
    category=UserWarning,
)

from pathlib import Path
import sys
import platform
import shutil
import numpy as np
import pipeline_functions
from viseme_sets import SET_MAPPING_DICT
import json
import os
import argparse

import importlib.util

# print("\n========== PIPELINE DEBUG ==========")
# print("EXECUTABLE:", sys.executable)

# for p in sys.path:
#     print("PATH:", p)

# for name in [
#     "whisperx",
#     "pyannote",
#     "torch",
#     "torchaudio",
#     "faster_whisper",
#     "ctranslate2",
# ]:
#     spec = importlib.util.find_spec(name)
#     print(name, "=>", spec)
#     if spec:
#         print("    ORIGIN:", spec.origin)

# print("====================================\n")

def init_espeak():
    from phonemizer.backend.espeak.wrapper import EspeakWrapper

    espeak = shutil.which("espeak-ng")

    if espeak is None:
        print("STATUS:NO_ESPEAK", flush=True)
        raise RuntimeError(
            "eSpeak NG was not found. Please install it and restart Blender."
        )
    
    EspeakWrapper.set_library(espeak)

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--file", required=True)
    parser.add_argument("--compute", default="CPU_COMPUTE")

    return parser.parse_known_args(sys.argv[sys.argv.index("--") + 1:])[0]

def main():
    import whisperx
    from phonemizer import phonemize

    settings_dict = {}
    args = parse_args()

    file_path = args.file
    compute_mode = args.compute

    print("PARSED FILE:", file_path)
  
    # Load settings.json as dict
    with open(file_path, 'r') as f:
        settings_dict = json.load(f)

    print("PROGRESS 0.1", flush=True)
    print("MESSAGE: Initializing variables...", flush=True)

    # Initialize important lip sync variables
    viseme_mapping = SET_MAPPING_DICT[settings_dict["viseme_set"]]
    parent_dir = os.path.dirname(file_path)
    # TODO: Implement GPU compute support
    # device = "cuda" if (compute_mode == "GPU_COMPUTE" and torch.cuda.is_available()) else "cpu"
    device = "cpu"

    # Allow legacy Python dependencies to work on modern NumPy versions
    if not hasattr(np, "NaN"):
        np.NaN = np.nan

    batch_size = 16 # reduce if low on GPU mem
    compute_type = "float16" if device == "gpu" else "int8" # change to "int8" if low on GPU mem (may reduce accuracy)
    
    print("PROGRESS 0.2", flush=True)
    print("MESSAGE: Transcribing audio...", flush=True)

    # Transcribe with original Whisper (batched)
    model = whisperx.load_model(settings_dict["model_size"], device, compute_type=compute_type, language="en")
    audio = whisperx.load_audio(settings_dict["audio_path"])
    
    print("PROGRESS 0.4", flush=True)

    result = model.transcribe(audio, batch_size=batch_size)
    transcript = result["segments"]

    # If no words detected in the audio
    if not transcript:
        print("STATUS:NO_WORDS", flush=True)
        print("PROGRESS 1.0", flush=True)
        return
    
    for segment in transcript:
        print("TEXT:", segment["text"])
        print("PHONEME:", phonemize(segment["text"]))

    print("PROGRESS 0.6", flush=True)
    print("MESSAGE: Phonemizing transcript...", flush=True)

    # Use Phonemize to get the transcript in terms of phonemes
    phone_transcript = [{
        "text": phonemize(segment["text"], backend="espeak", language="en-us"), 
        "start": segment["start"], 
        "end": segment["end"]
    } for segment in transcript]

    print("PROGRESS 0.7", flush=True)
    print("MESSAGE: Aligning transcript...", flush=True)

    # Align Whisper output
    aligner_model = "facebook/wav2vec2-large-960h-lv60"
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device, model_name=aligner_model)
    result = whisperx.align(phone_transcript, model_a, metadata, audio, device, return_char_alignments=True)

    print("PROGRESS 0.8", flush=True)
    print("MESSAGE: Saving viseme timing data...", flush=True)

    phoneme_timings = []
    for i in range(len(result["segments"])):
        phoneme_timings.extend(result["segments"][i].get('chars')[:-1])

    # Save a viseme timing list to viseme.json
    visemes = pipeline_functions.phonemes_to_visemes(phoneme_timings, viseme_mapping, settings_dict)
    viseme_data_path = os.path.join(parent_dir, "visemes.json")
    with open(viseme_data_path, 'w', encoding='utf-8') as f:
        text = json.dumps(visemes, ensure_ascii=False, indent=4)
        f.write(text)

    print("PROGRESS 0.9", flush=True)

    # Save a cleaned timing list to keyframe_data.json
    cleaned = pipeline_functions.cleanup_visemes(visemes, viseme_mapping, settings_dict)
    cleaned_data_path = os.path.join(parent_dir, "keyframe_data.json")
    with open(cleaned_data_path, 'w', encoding='utf-8') as f:
        text = json.dumps(cleaned, ensure_ascii=False, indent=4)
        f.write(text)
    
    print("PROGRESS 1.0", flush=True)

if __name__ == "__main__":
    init_espeak()
    main()