#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: ESP32S3LockingLock
# Filename: config
# Created on: 2022/9/6


import json


class DeviceConfig:

    def __init__(self, file_io, device_index_str):
        self.__file_io = file_io
        self.__device_index = device_index_str
        if self.__file_io.closed:
            self.__file_io = open(self.__file_io.name, "r+")
        self.__file_io.seek(0)
        json_dict = json.load(file_io)
        self.root_topic = json_dict["devices"][device_index_str]["mqtt_topic_root"]
        self.dynkey16_psk = json_dict["devices"][device_index_str]["dynkey16_psk"]
        self.storage = json_dict["devices"][device_index_str]["storage"]

    def save_config(self):
        if self.__file_io.closed:
            self.__file_io = open(self.__file_io.name, "r+")
        self.__file_io.seek(0)

        json_dict = json.load(self.__file_io)

        json_dict["devices"][self.__device_index]["mqtt_topic_root"] = self.root_topic
        json_dict["devices"][self.__device_index]["dynkey16_psk"] = self.dynkey16_psk
        json_dict["devices"][self.__device_index]["storage"] = self.storage


class Config:

    def __init__(self, filename):
        self.__file_io = open(filename, "r+")
        self.devices = []

        self.devices.append()

    def __loadDeviceConfig(self):
        if self.__file_io.closed:
            self.__file_io = open(self.__file_io.name, "r")
        self.__file_io.seek(0)
        data_raw = json.load(self.__file_io)

        for key in data_raw["devices"]: