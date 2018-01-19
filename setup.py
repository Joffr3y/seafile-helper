#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

import os
import seafile_helper

HERE = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(HERE, 'README.md'), encoding='utf-8') as f:
    description = f.read()

setup(
    name='seafile-helper',
    version=seafile_helper.__version__,
    description='Seafile-server and seahub helper for upgrade and deployment',
    long_description=description,
    url='https://github.com/jojotango/seafile-helper.git',
    author='Joffrey Darcq',
    author_email='j-off@live.fr',
    license='GPL3',
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3',
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
        'Natural Language :: French'
        'Operating System :: POSIX :: Linux'
        'Programming Language :: Python :: 3.6'
        'Topic :: Communications :: GitHub'
        ],
    keywords='python seafile seahub',
    entry_points={
        'console_scripts': ['seafile-helper = seafile_helper.helper:main']
    }
)