#!/usr/bin/env bash
# Build the Python backend as a single-file executable and place it where
# Tauri expects the sidecar binary.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BINARY_DIR="$REPO_ROOT/tauri-gui/src-tauri/binaries"
TARGET_TRIPLE="$(rustc -vV | sed -n 's|host: ||p')"
TARGET_NAME="jlc2kicadlib-helper-$TARGET_TRIPLE"

cd "$REPO_ROOT"

echo "Building sidecar with PyInstaller..."
uv run pyinstaller \
    --onefile \
    --name jlc2kicadlib-helper \
    --clean \
    --copy-metadata JLC2KiCadLib \
    sidecar/jlc2kicadlib_helper.py

mkdir -p "$BINARY_DIR"
SOURCE="$REPO_ROOT/dist/jlc2kicadlib-helper"
DESTINATION="$BINARY_DIR/$TARGET_NAME"

echo "Copying sidecar to $DESTINATION"
cp "$SOURCE" "$DESTINATION"

echo "Sidecar built successfully."
