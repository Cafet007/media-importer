#!/usr/bin/env bash
# Build Media Porter .app and .dmg for macOS
# Usage: ./build_mac.sh
# Requires: pip install pyinstaller create-dmg (brew install create-dmg)

set -e

echo "=== Media Porter — macOS Build ==="

# Clean previous build
rm -rf build dist

# Build .app bundle
echo "→ Building .app with PyInstaller..."
python3 -m PyInstaller MediaPorter_mac.spec --noconfirm

APP="dist/Media Porter.app"

if [ ! -d "$APP" ]; then
    echo "ERROR: $APP not found after build"
    exit 1
fi

echo "→ .app built: $APP"

# Create .dmg (requires: brew install create-dmg)
if command -v create-dmg &>/dev/null; then
    echo "→ Creating .dmg..."
    mkdir -p dist/dmg
    cp -r "$APP" dist/dmg/

    create-dmg \
        --volname "Media Porter" \
        --volicon "appicon.icns" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "Media Porter.app" 170 190 \
        --hide-extension "Media Porter.app" \
        --app-drop-link 430 190 \
        --no-internet-enable \
        "dist/MediaPorter-1.0.0-mac.dmg" \
        "dist/dmg/"

    echo "→ DMG: dist/MediaPorter-1.0.0-mac.dmg"
else
    echo "⚠  create-dmg not found. Install with: brew install create-dmg"
    echo "   .app is at: $APP"
fi

echo "=== Build complete ==="
