#!/bin/bash
set -e

cd "$(dirname "$0")/.."
ARCH=$(uname -m)
IMAGE_NAME="oracle-jdk-full-test"

echo "--------------------------------------------------"
echo "RUNNING EDGE-CASE TEST SUITE FOR ORACLE JDK 21"
echo "--------------------------------------------------"

DOCKER_BUILDKIT=1 docker build -t $IMAGE_NAME \
    --build-arg ARCH=$ARCH \
    -f testing/dockerfile .

echo ""
echo "FINAL RUN: Executing Compiled Java Code..."
docker run --rm $IMAGE_NAME

echo ""
echo "TEST SUITE COMPLETED SUCCESSFULLY!"
