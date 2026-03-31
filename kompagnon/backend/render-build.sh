#!/bin/bash
set -e

echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo "=== Installing Playwright Chromium ==="
python -m playwright install chromium
python -m playwright install-deps chromium || true

echo "=== Build complete ==="
