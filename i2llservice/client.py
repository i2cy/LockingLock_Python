#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: ESP32S3LockingLock
# Filename: client
# Created on: 2022/9/14

from i2cylib.network import Client
import json


class DeviceClient:

    def __init__(self, parent, device_root_topic):
        parent: I2LLClient
        device_root_topic: str
        self.__parent = parent
        self.root_topic = device_root_topic

    def isOnline(self):
        ret = False
        if self.__parent.connected:
            self.__parent.send(b"\x10" + self.root_topic.encode("utf-8"))
            fed = self.__parent.get(b"\x01", timeout=15)
            if fed is not None:
                ret = bool(fed[1])
        return ret

    def getStorage(self):
        ret = None
        if self.__parent.connected:
            self.__parent.send(b"\x11" + self.root_topic.encode("utf-8"))
            fed = self.__parent.get(b"\xe1", timeout=15)
            if fed is not None:
                ret = json.loads(fed[1:].decode("utf-8"))
        return ret

    def configurateDevice(self, storage=None):
        if storage is None:
            storage = self.getStorage()

        ret = False

        if self.__parent.connected and storage is not None:
            self.__parent.send(b"\x20" + self.root_topic.encode("utf-8")
                               + b"," + json.dumps(storage).encode("utf-8"))
            fed = self.__parent.get(b"\x01", timeout=15)
            if fed is not None:
                ret = bool(fed[1])

        return ret

    def calibrateMotor(self):
        ret = False
        if self.__parent.connected:
            self.__parent.send(b"\x21" + self.root_topic.encode("utf-8"))
            fed = self.__parent.get(b"\x01", timeout=15)
            if fed is not None:
                ret = bool(fed[1])
        return ret

    def unlock(self):
        ret = False
        if self.__parent.connected:
            self.__parent.send(b"\x22" + self.root_topic.encode("utf-8"))
            fed = self.__parent.get(b"\xd2", timeout=15)
            if fed is not None:
                ret = fed[1:]
        return ret

    def ringMotor(self):
        ret = False
        if self.__parent.connected:
            self.__parent.send(b"\x23" + self.root_topic.encode("utf-8"))
            fed = self.__parent.get(b"\x01", timeout=15)
            if fed is not None:
                ret = bool(fed[1])
        return ret


class I2LLClient(Client):

    def __init__(self, hostname, port=8421, psk="i2tcppsk",
                 logger=None, watchdog_timeout=15,
                 max_buffer_size=20):
        if not isinstance(psk, bytes):
            psk = psk.encode("utf-8")
        super(I2LLClient, self).__init__(hostname, port=port, key=psk,
                                         watchdog_timeout=watchdog_timeout,
                                         logger=logger,
                                         max_buffer_size=max_buffer_size)

        self.__ll_clients = []

    def __len__(self):
        if not len(self.__ll_clients):
            self.getAllRootTopics()
        return len(self.__ll_clients)

    def __iter__(self):
        if not len(self.__ll_clients):
            self.getAllRootTopics()
        return self.__ll_clients

    def __getitem__(self, item):
        if not len(self.__ll_clients):
            self.getAllRootTopics()
        return self.__ll_clients[item]

    def getAllRootTopics(self):
        assert self.connected
        pkg = b"\x01"
        self.send(pkg)
        pkg = self.get(b"\xf1", timeout=15)

        if pkg is not None:
            self.__ll_clients.clear()
            all_topics = json.loads(pkg[1:].decode())
            for i in all_topics:
                self.__ll_clients.append(DeviceClient(self, i))

    def getDeviceClient(self, root_topic):
        con: (DeviceClient, None)

        for con in self.__ll_clients:
            assert isinstance(con, DeviceClient)
            if con.root_topic in root_topic:
                return con
