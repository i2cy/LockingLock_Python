#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: ESP32S3LockingLock
# Filename: setup.py
# Created on: 2022/9/21


import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="i2llserver",  # Replace with your own name
    version="1.0.0",
    author="I2cy Cloud",
    author_email="i2cy@outlook.com",
    description="Server of LockingLock project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/i2cy/LockingLock_Python",
    project_urls={
        "Bug Tracker": "https://github.com/i2cy/LockingLock_Python/issues",
        "Source Code": "https://github.com/i2cy/LockingLock_Python",
        "Documentation": "https://github.com/i2cy/LockingLock_Python/blob/master/README.md"
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'i2cylib >= 1.12.0',
        'paho-mqtt'
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    entry_points={'console_scripts':
        [
            "i2llsrv = i2llservice.server:main"
        ]
    }
)
