#!/usr/bin/env python

from setuptools import setup, find_packages

with open("README.md", "r") as readme:
    long_description = readme.read()

setup(
    name='htcanalyze',
    version_config={
        "dirty_template": "{tag}",
        "dev_template": "{tag}.dev{ccount}"
    },
    setup_requires=["setuptools-git-versioning"],
    description='Analyze and summarize HTCondor use logs',
    long_description=long_description,
    author='Mathis Loevenich',
    author_email='m.loevenich@fz-juelich.de',
    packages=find_packages(),
    license='LICENSE',
    python_requires='>=3.6',
    install_requires=[
        "numpy",
        "htcondor>=8.8.6",
        "plotille>=3.7",
        "configargparse==1.2.3",
        "rich>=3.0.3",
        "wheel==0.37.0"
    ],
    tests_require=[
        'pytest>=6.0.1'
    ],
    entry_points={
        'console_scripts': [
            'htcanalyze=htcanalyze.main:main',
            'htcan=htcanalyze.main:main'
        ],
    },
    data_files=[
        ('config', ['config/htcanalyze.conf']),
        ('share/man/man1', ['man/man1/htcanalyze.1'])
    ]
)
