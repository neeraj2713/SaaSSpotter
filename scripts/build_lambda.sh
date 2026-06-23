#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build/lambda"
LAYER_DIR="${ROOT_DIR}/build/layer/python"

rm -rf "${ROOT_DIR}/build"
mkdir -p "${BUILD_DIR}" "${LAYER_DIR}"

pip install -r "${ROOT_DIR}/requirements.txt" -t "${LAYER_DIR}" --quiet
cp -r "${ROOT_DIR}/app" "${BUILD_DIR}/"

cd "${BUILD_DIR}"
zip -r "${ROOT_DIR}/build/api.zip" . -q
cd "${LAYER_DIR}"
zip -r "${ROOT_DIR}/build/layer.zip" . -q

echo "Built ${ROOT_DIR}/build/api.zip and ${ROOT_DIR}/build/layer.zip"
