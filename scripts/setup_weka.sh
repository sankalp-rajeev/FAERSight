#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .tools/weka
fetch() {
  local name="$1" url="$2" digest="$3"
  if [[ ! -f ".tools/weka/$name" ]]; then
    curl --fail --location --retry 3 "$url" --output ".tools/weka/$name"
  fi
  printf '%s  %s\n' "$digest" ".tools/weka/$name" | sha256sum --check -
}
fetch weka-stable-3.8.6.jar \
  https://repo.maven.apache.org/maven2/nz/ac/waikato/cms/weka/weka-stable/3.8.6/weka-stable-3.8.6.jar \
  932ea2f342b58fe45736389e9c426d5b5955e610d1f5f6485117f532068915e9
fetch bounce-0.18.jar \
  https://repo.maven.apache.org/maven2/nz/ac/waikato/cms/weka/thirdparty/bounce/0.18/bounce-0.18.jar \
  bffff1505335c02256b7ab2ccffbe4aa4d3ac9fe14c17557809b7c9d99d666ca
