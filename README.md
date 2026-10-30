# Mac Dictate 🎙️

Fast, local speech dictation tool optimized for **Apple Silicon (M-series)** using **MLX Whisper** and local **Ollama** post-processing.

## Key Features
- **GPU-Accelerated Transcription:** Uses `mlx-whisper` (`whisper-large-v3-turbo`) on Apple Silicon GPU/Neural Engine. Transcribes in ~1–2 seconds with zero cloud dependency.
- **Microphone Capture:** Native macOS audio recording via FFmpeg (`avfoundation`), automatically using your default system microphone (built-in, AirPods, external).
- **Domain-Aware Editing:** Ingests a local technical dictionary (`dictionary.txt`) to fix phonetic typos, company-specific jargon, and tech acronyms (e.g., *PeYa*, *GIS*, *BFF*, *Kafka*, *Go*, *PR*, *1-on-1*, *SBI*).
- **Preserves Original Language:** Fixes grammar, punctuation, and casing while strictly retaining the language spoken (Spanish, English, or Spanglish).
- **Instant Clipboard:** Copies clean text directly to macOS clipboard (`pbcopy`) so you can press `Cmd+V` immediately in Slack, your terminal, or an IDE.
- **Append to Notes:** Optionally appends dictated thoughts with a timestamp to an ongoing Markdown file.

---

## Prerequisites
- macOS on Apple Silicon (M1/M2/M3/M4)
- **FFmpeg:** `brew install ffmpeg`
- **Ollama:** `brew install ollama` (with model: `ollama pull gemma:2b`)
- **Python 3.10+** (or `uv`)

---

## Quick Installation

Clone or enter the repo and run:
```bash
./install.sh
```

This will:
1. Verify system dependencies (`ffmpeg`, `python3`, `ollama`).
2. Create a Python virtual environment and install `requirements.txt`.
3. Pull `gemma:2b` if not already present.
4. Symlink `dictate` to `~/.local/bin/dictate`.

---

## Usage

Simply run:
```bash
dictate
```
1. Speak into your microphone.
2. Press **[Enter]** or **[Ctrl+C]** to finish.
3. The cleaned transcription is printed in your terminal and copied to your clipboard (`Cmd+V`).

### Command-Line Options
```bash
# Append note to a markdown file (with timestamp)
dictate -o ~/feedback-tool/evidence/self/raw_notes.md

# Use a larger Ollama model (more accurate, slower)
dictate -m gemma4:26b

# Skip LLM post-processing (pure Whisper transcription)
dictate -m none

# Use a lighter/faster Whisper model
dictate -w mlx-community/whisper-tiny

# Transcribe an existing audio file
dictate -f recording.wav

# Do not copy to clipboard
dictate --no-copy
```

---

## Customizing the Dictionary
Edit `dictionary.txt` to add teammate names, project acronyms, or squad terms:
```
PedidosYa
PeYa
GIS
Checkout
BFF
Kafka
...
```
