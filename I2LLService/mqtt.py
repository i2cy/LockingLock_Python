#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: ESP32S3LockingLock
# Filename: mqtt
# Created on: 2022/8/22


from i2cylib.crypto import DynKey16
from paho.mqtt import client
from i2cylib.network.I2TCP import Server
import time
import threading

FEEDBACK_TOPIC = "feedback"
CMD_TOPIC = "cmd"


class PahoMqttSessionFlags(list):
    class __StatusObject(object):

        def __init__(self, is_connected, status):
            self.is_connected = is_connected
            self.status = status

    __flags = ["",
               "incorrect protocol version",
               "invalid client id",
               "server is not available",
               "invalid username or password",
               "unauthorised visit"]

    def __getitem__(self, item):
        assert isinstance(item, int)

        if not item:
            ret = self.__StatusObject(True, self.__flags[item])

        elif 0 < item < 6:
            ret = self.__StatusObject(False, self.__flags[item])

        else:
            ret = self.__StatusObject(False, "")

        return ret


class LLMqttClient:

    def __init__(self, parent, device_topic_root, watchdog_timeout=30):
        assert isinstance(parent, LLMqttAPI)
        self.__parent = parent
        self.__client = parent.getClient()
        assert isinstance(self.__client, client.Client)
        self.topic_root = "/" + "/".join([ele for ele in device_topic_root.split('/') if ele])

        self.__client.subscribe(self.topic_root + "/" + FEEDBACK_TOPIC)

        self.logger = parent.logger
        self.__log_header = "[MQTT] [{}]".format(self.topic_root)
        self.is_online = False
        self.__online_wdog_t0 = 0
        self.watchdog_timeout = watchdog_timeout
        self.__flow_cnt = 0
        self.__last_received_flow_cnt = 0

        threading.Thread(target=self.__onlineWatchdog).start()

    def __onlineWatchdog(self):
        while self.__parent.live:
            last = self.is_online
            self.is_online = time.time() - self.__online_wdog_t0 < self.watchdog_timeout
            if last != self.is_online:
                if self.is_online:
                    self.logger.INFO("{} device is now online".format(
                        self.__log_header))
                else:
                    self.logger.WARNING("{} device is now offline".format(
                        self.__log_header))
            time.sleep(2)

    def __feedWatchdog(self):
        self.__online_wdog_t0 = time.time()

    def __encodePackage(self, cmd_id, payload):
        status = False
        data = b""
        try:
            data += bytes((self.__flow_cnt,))
            self.__flow_cnt += 1
            data += bytes((cmd_id,))
            data += int(len(payload)).to_bytes(2, "big", signed=False)
            data += payload
            data += bytes((sum(data) % 256,))
            status = True
        except Exception as err:
            self.logger.WARNING("{} [decoder] failed to encode package, {}, raw hex: {}".format(
                self.__log_header, err, data.hex()))

        return status, data

    def __decodePackage(self, data):
        status = False
        cmd_id = 0
        payload = b""
        try:
            self.__last_received_flow_cnt = data[0]
            cmd_id = data[1]
            length = int().from_bytes(data[2:4], "big", signed=False)
            payload = data[4:4 + length]

            check_sum = sum(data[0:-1]) % 256
            status = check_sum == data[-1]

        except Exception as err:
            self.logger.WARNING("{} [decoder] failed to decode package, {}, raw hex: {}".format(
                self.__log_header, err, data.hex()))

        return status, cmd_id, payload

    def messageHandler(self, msg):
        if len(self.topic_root) > len(msg.topic) or self.topic_root != msg.topic[:len(self.topic_root)]:
            return

        self.logger.DEBUG("{} [handler] received message: {}".format(self.__log_header, msg.payload.hex()))

        status, cmd_id, payload = self.__decodePackage(msg.payload)

        if status:
            if cmd_id == 0x00:  # heartbeat
                self.__feedWatchdog()

            elif cmd_id == 0x01:  # time calibration
                self.caliDeviceTime()

            elif cmd_id == 0x02:  # request configuration
                self.configurateDevice()



    def caliDeviceTime(self):
        status, data = self.__encodePackage(0x11, int(time.time()).to_bytes(4, "big", signed=True))
        if status:
            self.__client.publish(self.topic_root + "/" + CMD_TOPIC, data)
            self.logger.DEBUG("{} [cmd] requesting time calibration".format(self.__log_header))

    def configurateDevice(self):
        status, data = self.__encodePackage(0x11, int(time.time()).to_bytes(4, "big", signed=True))
        if status:
            self.__client.publish(self.topic_root + "/" + CMD_TOPIC, data)
            self.logger.DEBUG("{} [cmd] requesting time calibration".format(self.__log_header))


class LLMqttAPI(Server):

    def __init__(self, client_id, username, pwd,
                 key, port, max_con=20, logger=None,
                 secured_connection=True, max_buffer_size=50,
                 watchdog_timeout=20):
        super(LLMqttAPI, self).__init__(key, port, max_con, logger, secured_connection,
                                        max_buffer_size, watchdog_timeout)
        self.__client = client.Client(client_id)
        self.__client.username_pw_set(username, pwd)

        self.__ll_clients = []

        self.connection_status = PahoMqttSessionFlags[255]

    def __onConnect(self, clt, userdata, flags, rc):
        self.connection_status = PahoMqttSessionFlags[rc]

    def __onMessage(self, clt, userdata, message):
        for con in self.__ll_clients:
            assert isinstance(con, LLMqttClient)
            con.messageHandler(message)

    def getClient(self):
        return self.__client

    def getMqttClient(self, root_topic):
        for con in self.__ll_clients:
            assert isinstance(con, LLMqttClient)
            if con.topic_root in root_topic:
                return con
