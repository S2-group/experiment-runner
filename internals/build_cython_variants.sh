#!/usr/bin/env bash
set -euo pipefail

root="${1:-/app/benchmarks}"

echo "Scanning for original.py under: $root"

python - <<'PY'
import sys
try:
    import Cython
    from Cython.Build import cythonize  # noqa
except Exception as e:
    print("ERROR: Cython not installed or broken:", e, file=sys.stderr)
    sys.exit(1)
print("Cython OK:", Cython.__version__)
PY

found_any=0

while IFS= read -r -d '' py; do
  found_any=1
  dir="$(dirname "$py")"
  base="$(basename "$py")"

  echo "==> Compiling: $py"
  (
    cd "$dir"
    python -m Cython.Build.Cythonize -3 -i \
      -X boundscheck=False \
      -X initializedcheck=False \
      -X cdivision=True \
      "$base"
  )
done < <(find "$root" -type f -name 'original.py' -print0)

if [[ "$found_any" -eq 0 ]]; then
  echo "No original.py files found under $root."
fi

echo "Done."
