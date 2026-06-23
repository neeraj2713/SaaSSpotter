#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build/lambda"
LAYER_DIR="${ROOT_DIR}/build/layer/python"

rm -rf "${ROOT_DIR}/build"
mkdir -p "${BUILD_DIR}" "${LAYER_DIR}"

echo "Installing Lambda dependencies (Linux x86_64 wheels)..."
pip install \
  -r "${ROOT_DIR}/requirements-lambda.txt" \
  -t "${LAYER_DIR}" \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.11 \
  --only-binary=:all: \
  --upgrade \
  --quiet

echo "Stripping unnecessary files from layer..."
find "${LAYER_DIR}" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find "${LAYER_DIR}" -type d -name 'tests' -exec rm -rf {} + 2>/dev/null || true
find "${LAYER_DIR}" -type d -name 'test' -exec rm -rf {} + 2>/dev/null || true
find "${LAYER_DIR}" -type f -name '*.pyc' -delete 2>/dev/null || true

# Already available in the AWS Lambda Python runtime
rm -rf "${LAYER_DIR}/boto3" "${LAYER_DIR}/botocore" "${LAYER_DIR}/s3transfer" 2>/dev/null || true

# google-generativeai pulls a huge discovery cache we don't need
rm -rf "${LAYER_DIR}/googleapiclient/discovery_cache" 2>/dev/null || true

cp -r "${ROOT_DIR}/app" "${BUILD_DIR}/"

cd "${BUILD_DIR}"
zip -r "${ROOT_DIR}/build/api.zip" . -q
cd "${ROOT_DIR}/build/layer"
zip -rq "${ROOT_DIR}/build/layer.zip" python

API_SIZE=$(du -h "${ROOT_DIR}/build/api.zip" | cut -f1)
LAYER_SIZE=$(du -h "${ROOT_DIR}/build/layer.zip" | cut -f1)
LAYER_BYTES=$(stat -f%z "${ROOT_DIR}/build/layer.zip" 2>/dev/null || stat -c%s "${ROOT_DIR}/build/layer.zip")

echo "Built ${ROOT_DIR}/build/api.zip (${API_SIZE})"
echo "Built ${ROOT_DIR}/build/layer.zip (${LAYER_SIZE})"

MAX_BYTES=70167211
if [ "${LAYER_BYTES}" -gt "${MAX_BYTES}" ]; then
  echo "ERROR: layer.zip exceeds AWS Lambda direct-upload limit (~67MB)." >&2
  echo "       Consider using Lambda container images or S3-based deployment." >&2
  exit 1
fi

echo "Layer size OK for direct upload (${LAYER_BYTES} bytes)"
