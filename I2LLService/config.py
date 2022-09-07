#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: ESP32S3LockingLock
# Filename: config
# Created on: 2022/9/6


import json


class DeviceConfig:

    def __init__(self, file_io, device_index_str, new=False):
        self.device_index = device_index_str
        self.__file_io = open(file_io.name, "r")
        json_dict = json.load(self.__file_io)
        if new:
            self.root_topic = "/esp32ll/dev_{}".format(device_index_str)
            self.dynkey16_psk = "dynkey16psk"
            self.storage = {"motor_offset": 0}
            self.save_config()
        else:
            self.root_topic = json_dict["devices"][device_index_str]["mqtt_topic_root"]
            self.dynkey16_psk = json_dict["devices"][device_index_str]["dynkey16_psk"]
            self.storage = json_dict["devices"][device_index_str]["storage"]
        self.__file_io.close()

    def __str__(self):
        return "<LL device, index: {}, topic: {}>".format(self.device_index, self.root_topic)

    def save_config(self):
        self.__file_io = open(self.__file_io.name, "r+")

        json_dict = json.load(self.__file_io)

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
        self.__file_io = open(filename, "r+")
        self.__file_io.close()
        self.__current_device_cnt = 0
        self.__loadDeviceConfig()

    def __str__(self):
        return "LockingLock server config object ({})".format(self.__file_io.name)

    def __loadDeviceConfig(self):
        self.__file_io = open(self.__file_io.name, "r")
        data_raw = json.load(self.__file_io)
        self.__file_io.close()

        for key in data_raw["devices"]:
            self.append(DeviceConfig(self.__file_io, key))
            if self.__current_device_cnt < int(key):
                self.__current_device_cnt = int(key)

    def addDevice(self, device_id=None):
        self.__current_device_cnt += 1
        print(self.__current_device_cnt)
        if device_id is None:
            device_id = self.__current_device_cnt
        device_id = str(device_id)

        new_device = DeviceConfig(self.__file_io, device_id, new=True)
        self.append(new_device)

        return new_device

    def removeDevice(self, device_id):
        device_id = str(device_id)
        target_index = 0

        for i, device in enumerate(self):
            assert isinstance(device, DeviceConfig)
            if device.device_index == device_id:
                target_index = i
                break

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

    def getDevice(self, index):
        ret = self[index]
        assert isinstance(ret, DeviceConfig)

        return ret


if __name__ == '__main__':
    conf = Config("sample/config.json")
    print("test file device count: {}".format(len(conf)))
    for dev_conf in conf:
        print("find device {} in config".format(dev_conf))

    print("adding new device")
    conf.addDevice()
    print("test file device count: {}".format(len(conf)))
    for dev_conf in conf:
        assert isinstance(dev_conf, DeviceConfig)
        print("find device {} in config".format(dev_conf))

    print("editing new added device")
    dev_conf = conf.getDevice(-1)
    dev_conf.root_topic = "/test/topic/edtied"
    dev_conf.save_config()

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
