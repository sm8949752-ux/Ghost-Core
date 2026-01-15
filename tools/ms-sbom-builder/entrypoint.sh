#!/bin/bash
set -e

if [ -z "$TARGET_URL" ] || [ -z "$PROJECT_NAME" ]; then
    echo "❌ Error: TARGET_URL and PROJECT_NAME environment variables are required."
    exit 1
fi

echo "🚀 Starting SBOM Generation Process..."
echo "📍 Target: $PROJECT_NAME"

WORKDIR="/tmp/work"
EXTRACT_DIR="/tmp/work/extracted"
OUTPUT_DIR="/output"
SOURCE_FILE="$WORKDIR/source.tar.gz"

mkdir -p $WORKDIR $EXTRACT_DIR

echo "⬇️  Downloading source from: $TARGET_URL"
curl -L "$TARGET_URL" -o "$SOURCE_FILE"

if [ ! -z "$EXPECTED_SHA256" ]; then
    echo "🔐 Verifying SHA256 Checksum..."

    CALCULATED_HASH=$(sha256sum "$SOURCE_FILE" | awk '{print $1}')

    if [ "$CALCULATED_HASH" != "$EXPECTED_SHA256" ]; then
        echo "❌ FATAL ERROR: Checksum Mismatch!"
        echo "   Expected: $EXPECTED_SHA256"
        echo "   Got:      $CALCULATED_HASH"
        echo "   The file might be corrupted or compromised."
        exit 1
    else
        echo "✅ Checksum Verified Successfully."
    fi
else
    echo "⚠️  No Checksum provided. Skipping verification."
fi

echo "📦 Extracting..."
tar -xf "$SOURCE_FILE" -C "$EXTRACT_DIR"

echo "🔍 Scanning..."
/usr/local/bin/sbom-tool generate \
    -b "$EXTRACT_DIR" \
    -bc "$EXTRACT_DIR" \
    -pn "$PROJECT_NAME" \
    -pv "${PROJECT_VERSION:-latest}" \
    -ps "GhostCore" \
    -nsb "https://ghost-core.local/$PROJECT_NAME" \
    -mi "SPDX:2.2" \
    >/dev/null 2>&1

echo "💾 Saving result..."
find "$EXTRACT_DIR" -name "manifest.spdx.json" -exec mv {} "$OUTPUT_DIR/$PROJECT_NAME.spdx.json" \;

echo "✅ Done! File saved to: $PROJECT_NAME.spdx.json"

rm -rf $WORKDIR
