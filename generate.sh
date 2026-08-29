#!/usr/bin/env bash

set -e

IMAGE_NAME="mycv-generator"

echo "======================================"
echo "        MyCV PDF Generator"
echo "======================================"

if ! command -v docker >/dev/null 2>&1; then
    echo ""
    echo "ERROR: Docker is not installed."
    echo ""
    echo "Install Docker Desktop:"
    echo "https://www.docker.com/products/docker-desktop/"
    echo ""
    exit 1
fi

echo ""
echo "Building generator environment..."

docker build \
    -t "$IMAGE_NAME" \
    .

echo ""
echo "Generating CVs..."

docker run \
    --rm \
    -v "$(pwd):/app" \
    "$IMAGE_NAME"

echo ""
echo "======================================"
echo "          Generation complete"
echo "======================================"

echo ""
echo "PDF files:"
ls -lh output/*.pdf

echo ""
echo "Website:"
echo "site/index.html"
echo "site/en.html"

