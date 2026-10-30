#!/usr/bin/env bash
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=== Installing Mac Dictate (${REPO_DIR}) ==="

# 1. OS check
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Error: Mac Dictate is optimized for macOS (Apple Silicon)."
  exit 1
fi

# 2. Check FFmpeg
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Error: ffmpeg not found. Install it with: brew install ffmpeg"
  exit 1
fi

# 3. Check Python
PYTHON_BIN=""
if command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="python3.11"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  echo "Error: Python 3 not found. Install Python 3.11+."
  exit 1
fi

# 4. Virtual environment with uv or python venv
cd "$REPO_DIR"
if command -v uv >/dev/null 2>&1; then
  echo "-> Setting up virtual environment with uv..."
  uv venv --python "$PYTHON_BIN" .venv
  uv pip install -r requirements.txt
else
  echo "-> Setting up virtual environment with $PYTHON_BIN -m venv..."
  "$PYTHON_BIN" -m venv .venv
  ./.venv/bin/pip install --upgrade pip
  ./.venv/bin/pip install -r requirements.txt
fi

# 5. Check Ollama
if ! command -v ollama >/dev/null 2>&1; then
  echo "Warning: ollama is not installed. LLM cleanup will be skipped unless installed."
  echo "Install it via: brew install ollama"
else
  echo "-> Checking Ollama model (gemma:2b)..."
  if ! ollama list 2>/dev/null | grep -q "gemma:2b"; then
    echo "Model gemma:2b not found. Pulling..."
    ollama pull gemma:2b || true
  fi
fi

# 6. Install CLI wrapper to ~/.local/bin
TARGET_BIN="$HOME/.local/bin"
mkdir -p "$TARGET_BIN"
chmod +x "$REPO_DIR/dictate"
ln -sf "$REPO_DIR/dictate" "$TARGET_BIN/dictate"

echo "=== Installation Successful! ==="
echo "Command dictate linked to $TARGET_BIN/dictate"
if [[ ":$PATH:" != *":$TARGET_BIN:"* ]]; then
  echo "Note: Ensure $TARGET_BIN is in your PATH (e.g. export PATH="\$HOME/.local/bin:\$PATH")"
fi
echo "Run dictate to start."
