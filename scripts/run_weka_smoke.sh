#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python -m faersight.cli weka-smoke \
  --jar "${WEKA_JAR:-.tools/weka/weka-stable-3.8.6.jar}" "$@"
