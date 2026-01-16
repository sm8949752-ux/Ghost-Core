#!/bin/bash
set -e

IMAGE_NAME="wolfi-bear-builder"
OUTPUT_DIR="packages"

echo "🚀 Starting Manual Bear Multi-Arch Build..."

docker run --privileged --rm tonistiigi/binfmt --install all
docker build -t $IMAGE_NAME .

if [ -z "$BEAR_SIGNING_KEY" ]; then
    echo "❌ ERROR: BEAR_SIGNING_KEY environment variable is not set!"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"
SIGNING_KEY="$OUTPUT_DIR/local-key.rsa"
echo "$BEAR_SIGNING_KEY" > "$SIGNING_KEY"

echo "🔑 Using signing key from ENV..."

docker run --rm --privileged \
    -v "$(pwd):/work" \
    -e BEAR_SIGNING_KEY="$BEAR_SIGNING_KEY" \
    $IMAGE_NAME build bear.yaml \
    --signing-key "$SIGNING_KEY" \
    --arch amd64,arm64 \
    --repository-append https://packages.wolfi.dev/os

rm -f "$SIGNING_KEY"

echo "🎉 Done! Check $OUTPUT_DIR/amd64/ and $OUTPUT_DIR/arm64/"


echo "  Running Melange for amd64 + arm64..."

docker run --rm --privileged \
    -v "$(pwd):/work" \
    $IMAGE_NAME build bear.yaml \
    --signing-key $KEY_NAME \
    --arch amd64,arm64 \
    --repository-append https://packages.wolfi.dev/os

echo "🎉 Done!"
echo "📦 Packages available in:"
echo "  ./packages/amd64/"
echo "  ./packages/arm64/"
