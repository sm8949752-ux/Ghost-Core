#!/bin/bash
set -e

TARGET="$1"
EXPECTED_SHA="$2"

if [ -z "$TARGET" ] || [ -z "$EXPECTED_SHA" ]; then
    echo "Usage: $0 <FILE_OR_URL> <SHA256>"
    exit 1
fi

check_hash() {
    local file="$1"
    local sha="$2"
    COMPUTED_SHA=$(sha256sum "$file" | awk '{print $1}')
    
    if [ "$COMPUTED_SHA" == "$sha" ]; then
        echo "OK: Checksum matched."
        return 0
    else
        echo "FAIL: Checksum mismatch."
        echo "Expected: $sha"
        echo "Computed: $COMPUTED_SHA"
        exit 1
    fi
}

if [[ "$TARGET" =~ ^https?:// ]]; then
    TEMP_FILE=$(mktemp)
    curl -sL "$TARGET" -o "$TEMP_FILE" || { echo "Download failed"; rm "$TEMP_FILE"; exit 1; }
    check_hash "$TEMP_FILE" "$EXPECTED_SHA"
    rm "$TEMP_FILE"
elif [ -f "$TARGET" ]; then
    check_hash "$TARGET" "$EXPECTED_SHA"
else
    echo "Error: Target not found."
    exit 1
fi