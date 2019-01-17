#
# Copyright (c) 2019, Magenta ApS
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import setuptools

setuptools.setup(
    name='os2mo_tools',
    version='0.1',
    description='Tools for communicating with OS2MO',
    author='Magenta ApS',
    author_email='info@magenta.dk',
    packages=setuptools.find_packages(),
    install_requires=[
        'requests==2.20.0',
        'cached_property==1.5.1'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MPL 2.0",
        "Operating System :: OS Independent",
    ]
)
