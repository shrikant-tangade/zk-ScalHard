#!/bin/bash
# =============================================================
#  UPTANE UPSTREAM FRAMEWORK SIMULATOR — LAUNCHER
#  Works on Ubuntu 20.04 / 22.04 / 24.04
#  Usage:  bash launch.sh
# =============================================================

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║   UPTANE UPSTREAM FRAMEWORK SIMULATOR           ║"
echo "  ║   Ed25519 · 101 ECUs · Director Repository      ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo -e "${RESET}"

# ── Step 1: Check Python 3.9+ ─────────────────────────────────
echo -e "${YELLOW}[1/5] Checking Python version...${RESET}"
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}ERROR: python3 not found. Run: sudo apt install python3${RESET}"
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo $PY_VERSION | cut -d. -f1)
PY_MINOR=$(echo $PY_VERSION | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]); then
    echo -e "${RED}ERROR: Python 3.9+ required. Found: Python ${PY_VERSION}${RESET}"
    exit 1
fi
echo -e "${GREEN}  ✓ Python ${PY_VERSION} found${RESET}"

# ── Step 2: Check project files ───────────────────────────────
echo -e "${YELLOW}[2/5] Checking project files...${RESET}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MISSING=0
for f in app.py uptane_engine.py; do
    if [ ! -f "$f" ]; then
        echo -e "${RED}  ✗ Missing: $f${RESET}"
        MISSING=1
    else
        echo -e "${GREEN}  ✓ Found: $f${RESET}"
    fi
done
if [ $MISSING -eq 1 ]; then
    echo -e "${RED}ERROR: Place all files in the same folder as this script.${RESET}"
    exit 1
fi

# ── Step 3: Virtual environment ───────────────────────────────
echo -e "${YELLOW}[3/5] Setting up virtual environment...${RESET}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}  ✓ venv created${RESET}"
else
    echo -e "${GREEN}  ✓ venv already exists${RESET}"
fi
source venv/bin/activate
echo -e "${GREEN}  ✓ venv activated${RESET}"

# ── Step 4: Install dependencies ─────────────────────────────
echo -e "${YELLOW}[4/5] Installing dependencies...${RESET}"
pip install --upgrade pip --quiet
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
else
    pip install "streamlit>=1.32.0" "cryptography>=41.0.0" --quiet
fi
python3 -c "import streamlit, cryptography; print('  \033[0;32m✓ streamlit', streamlit.__version__, '· cryptography', cryptography.__version__, '\033[0m')"

# ── Step 5: Launch ────────────────────────────────────────────
echo -e "${YELLOW}[5/5] Launching dashboard...${RESET}"
echo ""
echo -e "${CYAN}${BOLD}  ► Open browser at:  http://localhost:8501${RESET}"
echo -e "${CYAN}  ► Press Ctrl+C to stop${RESET}"
echo ""

streamlit run app.py \
    --server.port 8501 \
    --server.headless false \
    --server.address localhost \
    --theme.base dark \
    --theme.backgroundColor "#080d14" \
    --theme.primaryColor "#00d4ff" \
    --theme.textColor "#c8d8e8" \
    --theme.secondaryBackgroundColor "#0a1018"
