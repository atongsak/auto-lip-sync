import torch
import torchvision
import torchaudio
import whisperx
import numpy as np
from phonemizer import phonemize
from phonemizer.backend.espeak.wrapper import EspeakWrapper
import pipeline_functions
import viseme_sets

def main():
    WORK_DIR = "C:/Users/SPIRO/documents/auto-lip-sync/test_audios"

    audio_name = "i-live-alone"

    audio_file = f"{WORK_DIR}/{audio_name}.wav"

    print(audio_file)

    use_cuda_if_avail = True
    if use_cuda_if_avail and torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"

    # Have to do this for CPU
    if not hasattr(np, "NaN"):
        np.NaN = np.nan

    batch_size = 16 # reduce if low on GPU mem
    compute_type = "float16" if device == "gpu" else "int8" # change to "int8" if low on GPU mem (may reduce accuracy)

    # 1. Transcribe with original whisper (batched)
    model = whisperx.load_model("large-v2", device, compute_type=compute_type, language="en")

    audio = whisperx.load_audio(audio_file)
    result = model.transcribe(audio, batch_size=batch_size)
    transcript = model.transcribe(audio, batch_size=batch_size)["segments"]
    print(transcript) # before alignment

    # Use phonemize to get the transcript in terms of phonemes
    phone_transcript = [{"text": phonemize(segment["text"]), "start":segment["start"], "end":segment["end"]} for segment in transcript]

    # 2. Align whisper output
    aligner_model = "facebook/wav2vec2-large-960h-lv60"

    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device, model_name=aligner_model)

    result = whisperx.align(phone_transcript, model_a, metadata, audio, device, return_char_alignments=True)

    words = result["segments"][0].get('words')

    phonemes = phone_transcript[0]['text']

    phoneme_timings = result["segments"][0].get('chars')[:-1]

    print(phoneme_timings)

    # Example usage
    # audio_duration = pipeline_functions.get_duration_pydub(audio_file)

    # print(audio_duration)

    # visemes = pipeline_functions.phonemes_to_visemes(phoneme_timings, viseme_sets.MICROSOFT_22_MAPPING, audio_duration)

if __name__ == "__main__":
    # Testing this fix for Windows
    EspeakWrapper.set_library(r"C:\Program Files\eSpeak NG\libespeak-ng.dll")

    main()