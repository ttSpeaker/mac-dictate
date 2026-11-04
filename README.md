# Mac Dictate 🎙️

Fast, local speech dictation tool optimized for **Apple Silicon (M-series)** using **MLX Whisper** and local **LM Studio** (or **Ollama**) post-processing.

## Key Features
- **GPU-Accelerated Transcription:** Uses `mlx-whisper` (`whisper-large-v3-turbo`) on Apple Silicon GPU/Neural Engine. Transcribes in ~1–2 seconds with zero cloud dependency.
- **Microphone Capture:** Native macOS audio recording via FFmpeg (`avfoundation`), automatically using your default system microphone (built-in, AirPods, external).
- **Domain-Aware Editing:** Ingests a local technical dictionary (`dictionary.txt`) to fix phonetic typos, company-specific jargon, and tech acronyms (e.g., *PeYa*, *GIS*, *BFF*, *Kafka*, *Go*, *PR*, *1-on-1*, *SBI*, *Ariel Abut*, *Lucía Vázquez*).
- **Native LM Studio Integration:** Connects directly to LM Studio local server (`http://localhost:1234/v1/chat/completions`) with automatic model detection (e.g., Qwen 2.5 7B). Falls back gracefully to Ollama (`localhost:11434`) if LM Studio is offline.
- **Preserves Original Language:** Fixes grammar, punctuation, and casing while strictly retaining the language spoken (Spanish, English, or Spanglish).
- **Instant Clipboard:** Copies clean text directly to macOS clipboard (`pbcopy`) so you can press `Cmd+V` immediately in Slack, your terminal, or an IDE.
- **Append to Notes:** Optionally appends dictated thoughts with a timestamp to an ongoing Markdown file.

---

## Prerequisites
- macOS on Apple Silicon (M1/M2/M3/M4)
- **FFmpeg:** `brew install ffmpeg`
- **LM Studio:** https://lmstudio.ai/ with local server enabled, or **Ollama**: `brew install ollama`
- **Python 3.10+** (or `uv`)

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

# Choose LLM provider (auto, lmstudio, ollama, or none)
dictate -p lmstudio

# Specify model explicitly (default auto-detects loaded model)
dictate -m qwen/qwen2.5-vl-7b

# Skip LLM post-processing (pure Whisper transcription)
dictate -p none
```
