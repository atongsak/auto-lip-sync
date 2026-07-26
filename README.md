# Artist-Driven Auto Lip Sync Blender Add-on

### Generating first-pass lip sync animation from audio and user-defined mouth shapes using ASR, forced alignment, and phoneme processing.
Animating lip sync is a repetitive and time-consuming process in character animation. To animate dialogue, animators manually place and adjust mouth shapes by ear to match the audio.

This project accelerates that workflow by combining artist-defined viseme-pose asset mappings and audio with automatic speech recognition, forced alignment, and phoneme processing to produce a usable animation pass directly inside Blender.

## An Animator-Oriented Approach
Instead of replacing artistic control, this tool is designed to:
- Reduce the manual workload of lip sync animation
- Accelerate animation blocking by providing a strong starting point for refinement
- Keep artists in control of the final performance

## Key Features

### Animation
- 🎤 Generate lip sync animation from English dialogue (<25 MB audio)
- 🎞️ Automatically insert viseme keyframes into Blender's timeline
- 🧹 Clear existing lip sync keyframes before generating a new pass
- 😐 Automatically close the mouth after a configurable number of frames

### Rig Support
- 🎭 Map visemes to custom pose assets for any pose-based facial rig
- 😀 Supports both 22-viseme and 15-viseme workflows

### Workflow
- 📝 View the detected transcript when reviewing generated animation
- ⚙️ Built-in CPU dependency installer

## Planned Features
- 🚀 GPU acceleration for faster processing
- 🔊 Volume-based jaw amplitude controls
- 🖼️ Support for 2D animation image-plane reference workflows

## Setup

### 0. Install System Dependencies
Before installing the add-on, install the following system dependencies for your operating system.

#### Windows
Install **FFmpeg** using one of the following methods:
- **Recommended**: Open Command Prompt or PowerShell and run:
```
winget install -e --id Gyan.FFmpeg
```
- Alternative: Download and install FFmpeg manually from the official [FFmpeg Downloads](https://ffmpeg.org/download.html) page.

#### Mac
Install **FFmpeg** and **espeak-ng** using Homebrew:
```
brew install espeak-ng
brew install ffmpeg
```

## Contact
Annette Tongsak (annettetongsak@gmail.com)

For issues or feedback, please open a GitHub issue.

## Acknowledgements
This work utilizes [WhisperX](https://github.com/m-bain/whisperX) for audio transcription and [Wav2Vec2-Large-960h-Lv60](https://huggingface.co/facebook/wav2vec2-large-960h-lv60) for forced alignment. 

[Phonemizer](https://github.com/bootphon/phonemizer) with [espeak-ng backend](https://github.com/espeak-ng/espeak-ng) is used to convert detected transcripts to IPA phonemes.