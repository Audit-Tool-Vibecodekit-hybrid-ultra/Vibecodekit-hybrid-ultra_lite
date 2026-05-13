#!/bin/bash
# VibecodeKit Hybrid Ultra — Devin auto-setup
# This script is run at the start of each Devin session to set up VibecodeKit.

set -e

VCK_DIR="${HOME}/vibecodekit-tool"

# Clone or update VibecodeKit
if [ -d "$VCK_DIR" ]; then
    cd "$VCK_DIR" && git pull origin main --quiet 2>/dev/null || true
else
    git clone https://github.com/Audit-Tool-Vibecodekit-hybrid-ultra/Vibecodekit-hybrid-ultra_lite.git "$VCK_DIR"
fi

# Export environment
export PYTHONPATH="${VCK_DIR}/scripts:${PYTHONPATH:-}"
export VCK_ROOT="$VCK_DIR"

# Verify installation
python3 -m vibecodekit.cli doctor --root "$VCK_DIR" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f'VibecodeKit v{open(\"${VCK_DIR}/VERSION\").read().strip()} ready (exit_code={d[\"exit_code\"]})')
except:
    print('VibecodeKit installed (doctor check skipped)')
" 2>/dev/null || echo "VibecodeKit installed at $VCK_DIR"

echo "Usage: python3 -m vibecodekit.cli build plan \"<description>\" --target ./project"
