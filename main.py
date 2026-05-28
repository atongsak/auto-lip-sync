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
    render_start = settings_dict["render_start"]
    render_end = settings_dict["render_end"]
    viseme_set = settings_dict["viseme_set"]
    viseme_mapping = SET_MAPPING_DICT[viseme_set]
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
    limit_bytes = 25 * 1024 * 1024 # Whisper can handle files <25 MB

    progress = 0.1
    print(f"PROGRESS {progress}", flush=True)

    all_visemes = []

    # Run WhisperX on acceptable target audio strips
    # TODO: Rework so it doesn't skip audio files >25 MB when an acceptable file size is in the VSE
    # TODO: Consider sending an mp3 of only audio in the rendered VSE so it doesn't have to parse entire files
    for index, strip in enumerate(audio_strips):
        audio_file = strip.get("path")
        file_size = os.path.getsize(audio_file)

        # Skip audio strip if it exceeds 25 MB
        if file_size > limit_bytes:
            print(f"File is larger than 25 MB ({file_size} bytes)")
            continue

        # Skip audio strip if outside the rendered portion
        if strip["end"] <= render_start or strip["start"] >= render_end:
            continue

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

        visemes = pipeline_functions.phonemes_to_visemes(
            phoneme_timings, 
            viseme_mapping, 
            strip["start"], 
            strip["end"],
            strip["offset"],
            settings_dict
        )

        all_visemes.extend(visemes)

    viseme_data_path = os.path.join(parent_dir, f"all_visemes.json")
    with open(viseme_data_path, 'w', encoding='utf-8') as f:
        text = json.dumps(all_visemes, ensure_ascii=False, indent=4)
        f.write(text)

    cleaned = pipeline_functions.cleanup_visemes(
        all_visemes, 
        viseme_mapping,
        settings_dict
    )

    total = len(audio_strips)
    progress += (index + 1) / total
    print(f"PROGRESS {progress}", flush=True)

    cleaned_data_path = os.path.join(parent_dir, f"keyframe_data.json")
    with open(cleaned_data_path, 'w', encoding='utf-8') as f:
        text = json.dumps(cleaned, ensure_ascii=False, indent=4)
        f.write(text)


if __name__ == "__main__":
    # Testing this fix for Windows
    EspeakWrapper.set_library(r"C:\Program Files\eSpeak NG\libespeak-ng.dll")

    main()