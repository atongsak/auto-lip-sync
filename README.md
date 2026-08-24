# Artist-Driven Auto Lip Sync Blender Add-on

### Generating first-pass lip sync animation from audio and user-defined mouth shapes using automatic speech recognition, forced alignment, and phoneme processing.

>**Compatibility:** Blender **5.0+** (tested on Blender 5.0 and 5.1)

Animating lip sync is a repetitive and time-consuming process in character animation. To animate dialogue, animators manually place and adjust mouth shapes by ear to match the audio.

This project accelerates that workflow by combining artist-defined viseme-pose asset mappings and audio with automatic speech recognition, forced alignment, and phoneme processing to produce a usable animation pass directly inside Blender.

## An Animator-Oriented Approach
Instead of replacing artistic control, this tool is designed to:
- Reduce the manual workload of lip sync animation
- Accelerate animation blocking by providing a strong starting point for refinement
- Keep artists in control of the final performance

## Key Features

### Platform & Performance
- Windows x64 and macOS ARM64 support
- Blender 5.0+ support
- CPU inference support

### Audio & Transcription
- Generate lip sync animation from English dialogue (<25 MB)
- Choose the WhisperX ASR model size
- Control which audio channel to generate animation for

### Animation
- Automatically insert viseme keyframes into the timeline
- Choose where keyframes are inserted: a specific action or the currently open action
- Clear existing lip sync keyframes before insertion
- Automatically close the mouth after a configurable number of frames

### Rig Support
- Map visemes to custom pose assets for pose-based facial rigs
- Supports both 22-viseme and 15-viseme workflows

### Workflow & Setup
- Review the detected transcript alongside generated animation
- Built-in FFmpeg, eSpeak NG, and dependency checks
- Built-in validation for viseme mappings, rigs, and pose assets

## Planned Features
- GPU acceleration for faster processing
- Volume-based jaw amplitude controls
- Support for 2D animation image-plane reference workflows

## Setup

### Requirements
- Blender **5.0 or newer**
- Windows or macOS
- FFmpeg (all platforms)
- eSpeak NG (all platforms)

### 0. Install System Dependencies
Before installing the add-on, install the following system dependencies for your operating system.

#### Windows
Install **FFmpeg** using one of the following methods:
- **Recommended**: Open PowerShell as an Administrator and run:
```
winget install -e --id Gyan.FFmpeg
```
- Alternative: Download and install FFmpeg manually from the official [FFmpeg Downloads](https://ffmpeg.org/download.html) page.

Install **eSpeak NG** from the official [eSpeak NG Releases](https://github.com/espeak-ng/espeak-ng/releases) page:
1. Open the Assets section of the latest release and download `espeak-ng.msi`.
2. Double-click the downloaded `.msi` file to launch the installer.
3. Follow the setup wizard and click Install to complete the installation.

#### Mac
Install **FFmpeg** and **eSpeak NG** using Homebrew:
```
brew install espeak-ng
brew install ffmpeg
```

### 1. Install the Add-on
Download the latest ZIP archive from the **Releases** page. In Blender 5.0 or later, open **Edit → Preferences → Add-ons**, click ▼ in the top-right corner, select **Install from Disk…**, and choose the downloaded ZIP file.

## Contact
Annette Tongsak (annettetongsak@gmail.com)

For issues or feedback, please open a GitHub issue.

## Acknowledgements
This work utilizes [WhisperX](https://github.com/m-bain/whisperX) for audio transcription and [Wav2Vec2-Large-960h-Lv60](https://huggingface.co/facebook/wav2vec2-large-960h-lv60) for forced alignment. 

[Phonemizer](https://github.com/bootphon/phonemizer) with [eSpeak NG backend](https://github.com/espeak-ng/espeak-ng) is used to convert detected transcripts to IPA phonemes.