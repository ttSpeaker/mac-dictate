#!/usr/bin/env python3
"""
Mac Dictate — Fast Apple Silicon dictation with MLX Whisper and local Ollama cleanup.
"""
import os
import sys
import time
import signal
import tempfile
import argparse
import threading
import subprocess
from pathlib import Path

DEFAULT_OLLAMA_MODEL = "gemma:2b"
DEFAULT_WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"
SCRIPT_DIR = Path(__file__).parent.resolve()
DEFAULT_DICT_PATH = SCRIPT_DIR / "dictionary.txt"

# Module-level holder to preload whisper in background while recording
_mlx_whisper = None
_preload_error = None

def _preload_whisper_worker():
    global _mlx_whisper, _preload_error
    try:
        import mlx_whisper
        _mlx_whisper = mlx_whisper
    except Exception as e:
        _preload_error = e

def start_whisper_preload():
    t = threading.Thread(target=_preload_worker, daemon=True)
    t.start()

def load_dictionary(dict_path: Path) -> str:
    if not dict_path.exists():
        return ""
    with open(dict_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return ", ".join(lines)

def copy_to_clipboard(text: str):
    try:
        p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        p.communicate(text.encode("utf-8"))
        return True
    except Exception as e:
        print(f"[Warning] Failed to copy to clipboard: {e}", file=sys.stderr)
        return False

def record_audio(output_wav: str) -> bool:
    print("\n\033[1;36m🎤 Recording from default microphone...\033[0m", flush=True)
    print("\033[1;33m👉 Press [Enter] or [Ctrl+C] to stop and process.\033[0m\n", flush=True)

    cmd = [
        "ffmpeg",
        "-nostdin",
        "-y",
        "-f", "avfoundation",
        "-i", ":default",
        "-ar", "16000",
        "-ac", "1",
        output_wav
    ]

    p = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    try:
        input()
    except KeyboardInterrupt:
        pass
    finally:
        print("\n\033[1;32m🛑 Recording stopped. Processing audio...\033[0m", flush=True)
        if p.poll() is None:
            p.send_signal(signal.SIGINT)
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()

    return os.path.exists(output_wav) and os.path.getsize(output_wav) > 1000

def transcribe(wav_path: str, model_name: str, prompt_terms: str) -> str:
    global _mlx_whisper
    print(f"\033[1;33m⚡ Transcribing with MLX Whisper ({model_name.split('/')[-1]})...\033[0m", flush=True)
    
    if _mlx_whisper is None:
        import mlx_whisper
        _mlx_whisper = mlx_whisper

    t0 = time.time()
    kwargs = {"path_or_hf_repo": model_name}
    if prompt_terms:
        kwargs["prompt"] = prompt_terms
    result = _mlx_whisper.transcribe(wav_path, **kwargs)
    elapsed = time.time() - t0
    raw_text = result.get("text", "").strip()
    print(f"\033[90mTranscribed in {elapsed:.2f}s\033[0m", flush=True)
    return raw_text

def clean_with_ollama(text: str, model_name: str, dictionary_terms: str) -> str:
    if not model_name or model_name.lower() in ("none", "false", "0"):
        return text

    print(f"\033[1;35m🤖 Polishing text with Ollama ({model_name})...\033[0m", flush=True)
    import requests

    dict_hint = f"\nTechnical dictionary: {dictionary_terms}\n" if dictionary_terms else ""

    prompt = (
        "Eres un editor técnico de notas dictadas por voz.\n"
        "Tu tarea es limpiar la transcripción cruda:\n"
        "1. Corregir errores fonéticos y términos técnicos usando este diccionario: " + dictionary_terms + "\n"
        "2. Mantener ESTRICTAMENTE el mismo idioma original (español o inglés). NO TRADUZCAS.\n"
        "3. Corregir puntuación y mayúsculas.\n"
        "4. Devuelve ÚNICAMENTE el texto corregido, sin saludos, sin explicaciones ni markdown decorativo.\n\n"
        f"Texto crudo:\n{text}\n\n"
        "Texto corregido:"
    )

    t0 = time.time()
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2
                }
            },
            timeout=60
        )
        elapsed = time.time() - t0
        if resp.status_code == 200:
            cleaned = resp.json().get("response", "").strip()
            print(f"\033[90mFormatted in {elapsed:.2f}s\033[0m", flush=True)
            return cleaned if cleaned else text
        elif resp.status_code == 404:
            print(f"[Warning] Ollama model '{model_name}' not found. Run: ollama pull {model_name}", file=sys.stderr)
            return text
        else:
            print(f"[Warning] Ollama returned status {resp.status_code}, keeping raw text.", file=sys.stderr)
            return text
    except Exception as e:
        print(f"[Warning] Ollama unavailable ({e}), keeping raw text.", file=sys.stderr)
        return text

def main():
    # Preload whisper module in background while user speaks
    preload_thread = threading.Thread(target=_preload_whisper_worker, daemon=True)
    preload_thread.start()

    parser = argparse.ArgumentParser(description="Mac Dictate: Local speech dictation with Whisper and Ollama.")
    parser.add_argument("-f", "--file", help="Path to existing audio file to transcribe instead of recording.")
    parser.add_argument("-m", "--model", default=DEFAULT_OLLAMA_MODEL, help=f"Ollama model for cleanup (default: {DEFAULT_OLLAMA_MODEL}, or 'none').")
    parser.add_argument("-w", "--whisper-model", default=DEFAULT_WHISPER_MODEL, help=f"MLX Whisper model (default: {DEFAULT_WHISPER_MODEL}).")
    parser.add_argument("-o", "--output", help="Optional markdown file to append transcription to.")
    parser.add_argument("-d", "--dict", default=str(DEFAULT_DICT_PATH), help="Path to dictionary terms file.")
    parser.add_argument("--no-copy", action="store_true", help="Do not copy result to clipboard.")

    args = parser.parse_args()

    dict_terms = load_dictionary(Path(args.dict))

    temp_wav = None
    if args.file:
        wav_path = args.file
        if not os.path.exists(wav_path):
            print(f"Error: File not found: {wav_path}", file=sys.stderr)
            sys.exit(1)
    else:
        fd, temp_wav = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        wav_path = temp_wav
        success = record_audio(wav_path)
        if not success:
            print("No audio captured.", file=sys.stderr)
            if temp_wav and os.path.exists(temp_wav):
                os.remove(temp_wav)
            sys.exit(0)

    try:
        raw = transcribe(wav_path, args.whisper_model, dict_terms)
        if not raw:
            print("\033[90mNo speech detected.\033[0m")
            return

        print(f"\n\033[90m[Raw Whisper]\033[0m: {raw}")

        final_text = clean_with_ollama(raw, args.model, dict_terms)

        print("\n" + "=" * 60)
        print("\033[1;32m📝 Final Result:\033[0m")
        print(final_text)
        print("=" * 60 + "\n")

        if not args.no_copy:
            if copy_to_clipboard(final_text):
                print("\033[1;34m📋 Copied to clipboard!\033[0m (Paste with Cmd+V)")

        if args.output:
            out_path = Path(args.output).expanduser().resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            entry = f"\n### Note ({timestamp})\n\n{final_text}\n"
            with open(out_path, "a", encoding="utf-8") as f:
                f.write(entry)
            print(f"\033[1;32m💾 Appended to:\033[0m {out_path}")

    finally:
        if temp_wav and os.path.exists(temp_wav):
            os.remove(temp_wav)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\033[90mCancelled.\033[0m")
        sys.exit(0)
