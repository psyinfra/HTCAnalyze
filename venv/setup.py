#!/usr/bin/env python
#

# Todo: test

from setuptools import setup, find_packages

setup(name='HTCompact',
      version='1.0.3',
      description='HTCondor summariser script',
      author='Mathis Loevenich',
      url="https://jugit.fz-juelich.de/inm7/infrastructure/loony_tools/htcondor-summariser-script.git",
      author_email='m.loevenich@fz-juelich.de',
      #packages=find_packages(exclude=["re", "sys", "os", "getopt", "datetime", "logging", "configparser", "pandas", "tabulate"]),
      packages=find_packages(),
      dependency_links=['https://github.com/astanin/python-tabulate.git'],
      license='LICENSE.txt',
    )