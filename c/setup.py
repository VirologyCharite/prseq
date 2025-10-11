#!/usr/bin/env python3
"""Setup script for building the prseq_c Python extension module."""

from setuptools import setup, Extension

prseq_c_extension = Extension(
    'prseq_c',
    sources=[
        'prseq_c_module.c',
        'fasta_reader.c',
        'fastq_reader.c'
    ],
    include_dirs=['.'],
    extra_compile_args=['-O3', '-std=c99'],
)

setup(
    name='prseq_c',
    version='0.0.1',
    description='C-based FASTA/FASTQ readers with Python bindings',
    ext_modules=[prseq_c_extension],
)
