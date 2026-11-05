#!/usr/bin/env bash
# Regenerate the fake example files and scan them.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 scripts/make_demo_data.py
echo
echo "=== Scanning leaky files ==="
genoscan scan examples/leaky.vcf examples/leaky.fastq || echo "(exit code $? = findings at or above --fail-on)"
echo
echo "=== Scanning clean files ==="
genoscan scan examples/clean.vcf examples/clean.fastq && echo "(exit code 0 = nothing serious)"
