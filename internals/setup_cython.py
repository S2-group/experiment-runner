from setuptools import setup
from Cython.Build import cythonize
import glob
import os

pyx_files = []
for benchmark_dir in glob.glob("benchmarks/*/"):
    pyx_pattern = os.path.join(benchmark_dir, "cython_variant.pyx")
    pyx_files.extend(glob.glob(pyx_pattern))

setup(
    ext_modules=cythonize(pyx_files, compiler_directives={'language_level': 3}),
    zip_safe=False,
)