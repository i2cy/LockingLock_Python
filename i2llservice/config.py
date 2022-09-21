#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: ESP32S3LockingLock
# Filename: config
# Created on: 2022/9/6


import json
import os
from i2cylib.utils import i2TecHome, DirTree


class DeviceConfig:

    def __init__(self, file_io, device_index_str, new=False):
        self.device_index = device_index_str
        self.__file_io = open(file_io.name, "r")
        json_dict = json.load(self.__file_io)
        if new:
            self.root_topic = "/esp32ll/dev_{}".format(device_index_str)
            self.dynkey16_psk = "dynkey16psk"
            self.storage = {"motor_offset": 0}
            self.saveConfig()
        else:
            self.root_topic = json_dict["devices"][device_index_str]["mqtt_topic_root"]
            self.dynkey16_psk = json_dict["devices"][device_index_str]["dynkey16_psk"]
            self.storage = json_dict["devices"][device_index_str]["storage"]
        self.__file_io.close()

    def __str__(self):
        return "<LL device, index: {}, topic: {}>".format(self.device_index, self.root_topic)

    def saveConfig(self):
        self.__file_io = open(self.__file_io.name, "r+")
        json_dict = json.load(self.__file_io)
        self.__file_io.close()

        new_device_dict = {self.device_index: {
            "mqtt_topic_root": self.root_topic,
            "dynkey16_psk": self.dynkey16_psk,
            "storage": self.storage
        }}
        json_dict["devices"].update(new_device_dict)

        self.__file_io = open(self.__file_io.name, "w")
        json.dump(json_dict, self.__file_io, indent=2)
        self.__file_io.close()


class Config(list):

    def __init__(self, filename):
        super(Config, self).__init__([])

        if os.path.exists(filename) and os.path.isfile(filename):
            self.__file_io = open(filename, "r+")
            json_dict = json.load(self.__file_io)

            self.mqtt_host = json_dict["mqtt_host"]
            self.mqtt_port = json_dict["mqtt_port"]
            self.mqtt_user = json_dict["mqtt_user"]
            self.mqtt_password = json_dict["mqtt_password"]
            self.i2tcp_port = json_dict["i2tcp_port"]
            self.i2tcp_psk = json_dict["i2tcp_psk"]
            self.log_file = json_dict["log_file"]
            self.log_level = json_dict["log_level"]
            self.mqtt_client_id = json_dict["mqtt_client_id"]

            self.__file_io.close()

        else:
            self.__file_io = open(filename, "w")
            self.__file_io.close()
            self.mqtt_host = "127.0.0.1"
            self.mqtt_port = 1883
            self.mqtt_user = "admin"
            self.mqtt_password = "admin"
            self.mqtt_client_id = "I2LL-Service"
            self.i2tcp_port = 8421
            self.i2tcp_psk = "i2tcppsk"
            self.log_file = DirTree(i2TecHome(), "i2ll", "i2ll.log").asPosix()
            self.log_level = "DEBUG"

            self.saveConfig(new=True)

        self.__current_device_cnt = -1
        self.__loadDeviceConfig()

    def __str__(self):
        return "LockingLock server config object ({})".format(self.__file_io.name)

    def __loadDeviceConfig(self):
        self.__file_io = open(self.__file_io.name, "r")
        data_raw = json.load(self.__file_io)
        self.__file_io.close()

        devices = list(data_raw["devices"].keys())
        devices.sort()

        for key in devices:
            self.append(DeviceConfig(self.__file_io, key))
            if self.__current_device_cnt < int(key):
                self.__current_device_cnt = int(key)

    def addDevice(self, device_id=None):
        self.__current_device_cnt += 1
        # print(self.__current_device_cnt)
        if device_id is None:
            device_id = self.__current_device_cnt
        device_id = str(device_id)

        new_device = DeviceConfig(self.__file_io, device_id, new=True)
        self.append(new_device)

        return new_device

    def removeDevice(self, device_id):
        device_id = str(device_id)
        target_index = 0
        succeed = False

        for i, device in enumerate(self):
            assert isinstance(device, DeviceConfig)
            if device.device_index == device_id:
                target_index = i
                succeed = True
                break

        if succeed:
            self.pop(target_index)

            if self.__file_io.closed:
                self.__file_io = open(self.__file_io.name, "r")
            self.__file_io.seek(0)
            data_raw = json.load(self.__file_io)
            self.__file_io.close()

            data_raw["devices"].pop(device_id)

            self.__file_io = open(self.__file_io.name, "w")
            json.dump(data_raw, self.__file_io, indent=2)
            self.__file_io.close()

        return succeed

    def getDevice(self, index: int):
        ret = self[index]
        assert isinstance(ret, DeviceConfig)

        return ret

    def saveConfig(self, new=False):
        if new:
            json_dict = {}
        else:
            self.__file_io = open(self.__file_io.name, "r+")
            json_dict = json.load(self.__file_io)
            self.__file_io.close()

        new_device_dict = {
            "mqtt_host": self.mqtt_host,
            "mqtt_port": self.mqtt_port,
            "mqtt_user": self.mqtt_user,
            "mqtt_password": self.mqtt_password,
            "i2tcp_port": self.i2tcp_port,
            "i2tcp_psk": self.i2tcp_psk,
            "log_file": self.log_file,
            "log_level": self.log_level,
            "mqtt_client_id": self.mqtt_client_id
        }
        json_dict.update(new_device_dict)
        if new:
            json_dict.update({"devices": {}})

        self.__file_io = open(self.__file_io.name, "w")
        json.dump(json_dict, self.__file_io, indent=2)
        self.__file_io.close()


if __name__ == '__main__':
    conf = Config("sample/config.json")
    print("test file device count: {}".format(len(conf)))
    for dev_conf in conf:
        print("find device {} in config".format(dev_conf))

    print("adding 2 new device")
    conf.addDevice()
    conf.addDevice()
    print("test file device count: {}".format(len(conf)))
    for dev_conf in conf:
        assert isinstance(dev_conf, DeviceConfig)
        print("find device {} in config".format(dev_conf))

    print("editing new added device")
    dev_conf = conf.getDevice(-1)
    dev_conf.root_topic = "/test/topic/edtied"
    dev_conf.saveConfig()

    f = open("sample/config.json", "r")
    print("displaying config now:")
    print(f.read())
    f.close()

    print("removing device")
    conf.removeDevice(str(len(conf) - 1))

    print("test file device count: {}".format(len(conf)))
    for dev_conf in conf:
        assert isinstance(dev_conf, DeviceConfig)
        print("find device {} in config".format(dev_conf))
