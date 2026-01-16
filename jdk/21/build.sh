#!/bin/bash
set -e

IMAGE_NAME="wolfi-jdk-builder"
YAML_CONFIG="oracle-jdk-21.yaml"
OUTPUT_DIR="packages"
JDK_SIGNING_KEY=$BEAR_SIGNING_KEY
echo "Starting Oracle JDK Multi-Arch Build for Wolfi OS..."

echo "Ensuring multi-arch support is enabled..."
docker run --privileged --rm tonistiigi/binfmt --install all

echo "Building the melange builder image: $IMAGE_NAME..."
docker build -t $IMAGE_NAME .

if [ -z "$JDK_SIGNING_KEY" ]; then
    echo "ERROR: JDK_SIGNING_KEY environment variable is not set!"
    echo "Please set it with your private key to sign the packages."
    exit 1
fi

mkdir -p "$OUTPUT_DIR"
SIGNING_KEY_PATH="$OUTPUT_DIR/local-key.rsa"
echo "$JDK_SIGNING_KEY" > "$SIGNING_KEY_PATH"

echo "Signing key has been prepared."

echo "Running Melange build for amd64 and arm64..."
docker run --rm --privileged \
    -v "$(pwd):/work" \
    $IMAGE_NAME build $YAML_CONFIG \
    --signing-key "$SIGNING_KEY_PATH" \
    --arch amd64,arm64 \
    --repository-append https://packages.wolfi.dev/os

rm -f "$SIGNING_KEY_PATH"

echo "Build complete!"
echo "Packages are available in the following directories:"
echo "  ./$OUTPUT_DIR/amd64/"
echo "  ./$OUTPUT_DIR/arm64/"
