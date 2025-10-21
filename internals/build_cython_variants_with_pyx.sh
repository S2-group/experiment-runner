#!/usr/bin/env bash
set -euo pipefail

root="${1:-/app/benchmarks}"

echo "Scanning for cython_variant.pyx under: $root"
found_any=0

# Requires bash for -d ''; we install bash in the Dockerfile.
while IFS= read -r -d '' pyx; do
  found_any=1
  dir="$(dirname "$pyx")"
  echo "==> Building in: $dir"
  (
    cd "$dir"
    python - <<'PY'
from setuptools import setup, Extension
from Cython.Build import cythonize

setup(
    name="cy_build",
    ext_modules=cythonize(
        [Extension("cython_variant", sources=["cython_variant.pyx"])],
        language_level="3",
        compiler_directives=dict(
            boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False
        ),
    ),
    script_args=["build_ext", "--inplace"],
)
PY
  )
done < <(find "$root" -type f -name 'cython_variant.pyx' -print0)

if [[ "$found_any" -eq 0 ]]; then
  echo "No cython_variant.pyx files found under $root."
fi

echo "Done."
