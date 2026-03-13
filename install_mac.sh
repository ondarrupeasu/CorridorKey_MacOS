#!/bin/bash

echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║        CorridorKey — Mac Installer        ║"
echo "║     Neural green screen keying · MLX     ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()  { echo -e "${GREEN}✓ $1${NC}"; }
err() { echo -e "${RED}✗ $1${NC}"; echo ""; echo "Installation failed. Please try again."; exit 1; }
inf() { echo -e "${YELLOW}→ $1${NC}"; }

if [[ $(uname -m) != "arm64" ]]; then
    err "This installer requires a Mac with Apple Silicon (M1/M2/M3/M4)"
fi
ok "Apple Silicon detected"

RAM_GB=$(sysctl hw.memsize | awk '{print int($2/1024/1024/1024)}')
if [ "$RAM_GB" -lt 24 ]; then
    err "At least 24GB RAM required. Your Mac has ${RAM_GB}GB."
fi
ok "RAM OK (${RAM_GB}GB)"

if ! command -v uv &> /dev/null; then
    inf "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.local/bin/env"
    ok "uv installed"
else
    ok "uv already installed"
fi
source "$HOME/.local/bin/env" 2>/dev/null || true

CKPATH="$HOME/CorridorKey"
if [ -d "$CKPATH" ]; then
    inf "CorridorKey already exists — updating..."
    cd "$CKPATH" && git pull
else
    inf "Downloading CorridorKey..."
    git clone https://github.com/nikopueringer/CorridorKey "$CKPATH" || err "Failed to clone repository"
    cd "$CKPATH"
fi
ok "Repository ready"

inf "Installing Python dependencies (may take a few minutes)..."
cd "$CKPATH"
uv sync || err "Failed to install dependencies"
ok "Dependencies installed"

inf "Installing MLX backend..."
uv pip install corridorkey-mlx@git+https://github.com/nikopueringer/corridorkey-mlx.git || err "Failed to install MLX"
ok "MLX backend installed"

inf "Installing GUI extras..."
uv pip install imageio || true
ok "Extras installed"

MODEL_DIR="$CKPATH/CorridorKeyModule/checkpoints"
MODEL_FILE="$MODEL_DIR/CorridorKey.pth"
mkdir -p "$MODEL_DIR"
if [ -f "$MODEL_FILE" ]; then
    ok "AI model already downloaded"
else
    inf "Downloading AI model (~382MB)..."
    curl -L --progress-bar \
         "https://huggingface.co/nikopueringer/CorridorKey_v1.0/resolve/main/CorridorKey_v1.0.pth" \
         -o "$MODEL_FILE" || err "Failed to download model"
    ok "AI model downloaded"
fi

# Copiar GUI desde el .app
GUI_SRC="$HOME/Desktop/CorridorKey.app/Contents/Resources/corridorkey_gui.py"
if [ -f "$GUI_SRC" ]; then
    cp "$GUI_SRC" "$CKPATH/corridorkey_gui.py"
    ok "GUI installed"
fi

echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║       ✅  Installation complete!          ║"
echo "║   Open CorridorKey from your Desktop     ║"
echo "╚═══════════════════════════════════════════╝"
echo ""
