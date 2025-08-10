#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Setup script for Rubik Ultimate Solver
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='rubik-ultimate',
    version='1.0.0',
    author='Rubik Ultimate Team',
    author_email='rubik.ultimate@example.com',
    description='Ultimate Rubik\'s Cube Solver with webcam scanning and 3D visualization',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/rubik-ultimate',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Games/Entertainment :: Puzzle Games',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.4.3',
            'pytest-cov>=4.1.0',
            'black>=23.11.0',
            'flake8>=6.1.0',
            'sphinx>=7.2.6',
            'sphinx-rtd-theme>=1.3.0',
        ],
        'cuda': [
            'cupy>=12.2.0',  # For GPU acceleration
        ],
    },
    entry_points={
        'console_scripts': [
            'rubik-ultimate=src.main:main',
            'rubik-cli=src.cli:main',
        ],
        'gui_scripts': [
            'rubik-gui=src.main:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['*.json', '*.txt', '*.ttf', '*.png', '*.qss'],
        'translations': ['*.json'],
        'assets': ['**/*'],
    },
    zip_safe=False,
    keywords='rubik cube solver webcam opencv 3d visualization kociemba thistlethwaite',
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/rubik-ultimate/issues',
        'Source': 'https://github.com/yourusername/rubik-ultimate',
        'Documentation': 'https://rubik-ultimate.readthedocs.io/',
    },
)