#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: ESP32S3LockingLock
# Filename: mqtt
# Created on: 2022/8/22


from i2cylib.crypto import DynKey16
from paho.mqtt import client


class LLMqttAPI(client):

    def __init__(self, client_id):
