#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: ESP32S3LockingLock
# Filename: mqtt
# Created on: 2022/8/22


from i2cylib.crypto import DynKey16
from paho.mqtt import client
from i2cylib.network.I2TCP import Server
from i2cylib.utils import Logger

if __name__ == "__main__":
    from config import DeviceConfig, Config
else:
    from .config import DeviceConfig, Config

import time
import threading

FEEDBACK_TOPIC = "data"
CMD_TOPIC = "request"


class PahoMqttSessionFlags(object):
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

    def __init__(self):
        pass

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

    def __init__(self, parent, device_config, watchdog_timeout=30):
        assert isinstance(parent, LLServer)
        assert isinstance(device_config, DeviceConfig)
        self.__parent = parent
        self.__client = parent.getMqttClient()
        assert isinstance(self.__client, client.Client)
        self.device_config = device_config
        self.topic_root = self.device_config.root_topic
        if self.topic_root[-1] == "/":
            self.topic_root = self.topic_root[:-1]

        self.logger = parent.logger
        self.__log_header = "[MQTT] [{}]".format(self.topic_root)
        self.is_online = False
        self.__online_wdog_t0 = 0
        self.watchdog_timeout = watchdog_timeout
        self.__flow_cnt = 0
        self.__last_received_flow_cnt = 0
        self.__flag_topic_ok = False

        try:
            self.__client.subscribe(self.topic_root + "/" + FEEDBACK_TOPIC)
            self.logger.INFO("{} feedback topic \"{}\" subscribed".format(
                self.__log_header, self.topic_root + "/" + FEEDBACK_TOPIC))
            self.__flag_topic_ok = True
        except Exception as err:
            self.logger.ERROR("{} failed to subscribe topic, {}".format(self.__log_header, err))

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

            if not self.__flag_topic_ok:
                try:
                    self.__client.subscribe(self.topic_root + "/" + FEEDBACK_TOPIC)
                    self.__flag_topic_ok = True
                except Exception as err:
                    self.logger.ERROR("{} failed to subscribe topic, {}".format(self.__log_header, err))

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
                self.__deviceTimeCheck(payload)

            elif cmd_id == 0x01:  # time calibration
                self.caliDeviceTime()

            elif cmd_id == 0x02:  # request configuration
                self.configurateDevice()

            elif cmd_id == 0x30:  # calibration data
                self.__storageOffset(payload)
                self.sendOkFlag()

            elif cmd_id == 0xff:  # ok flag from device
                pass

    def __storageOffset(self, feedback_payload):
        offset = int().from_bytes(feedback_payload, "little", signed=False)
        self.logger.INFO("{} device motor calibrated, offset: {}".format(self.__log_header, offset))
        self.device_config.storage["motor_offset"] = offset


    def __deviceTimeCheck(self, feedback_payload):
        now = time.time()
        feedback = int().from_bytes(feedback_payload, "little", signed=False)
        if abs(now - feedback) > 15:
            self.logger.INFO("{} device time {}, is not synchronised with server, real time now {}".format(
                self.__log_header, feedback, int(now)
            ))
            self.caliDeviceTime()

    def sendOkFlag(self):
        status, data = self.__encodePackage(0xee, int(time.time()).to_bytes(4, "big", signed=True))
        if status:
            self.__client.publish(self.topic_root + "/" + CMD_TOPIC, data)
            self.logger.DEBUG("{} [cmd] sending ok flag".format(self.__log_header))

    def caliDeviceTime(self):
        status, data = self.__encodePackage(0x11, int(time.time()).to_bytes(4, "little", signed=True))
        if status:
            self.__client.publish(self.topic_root + "/" + CMD_TOPIC, data)
            self.logger.DEBUG("{} [cmd] requesting time calibration".format(self.__log_header))

    def configurateDevice(self):
        status, data = self.__encodePackage(0x12,
                                            int(self.device_config.storage["motor_offset"]).to_bytes(4, "big",
                                                                                                     signed=True))
        if status:
            self.__client.publish(self.topic_root + "/" + CMD_TOPIC, data)
            self.logger.DEBUG("{} [cmd] configuring device".format(self.__log_header))

    def caliMotorOffset(self):
        status, data = self.__encodePackage(0x13, int(time.time()).to_bytes(4, "big", signed=True))

        if status:
            self.__client.publish(self.topic_root + "/" + CMD_TOPIC, data)
            self.logger.DEBUG("{} [cmd] calibrating motor offset".format(self.__log_header))

class LLServer(Server):

    def __init__(self, config,
                 max_connections=20,
                 secured_connection=True, max_buffer_size=50,
                 watchdog_timeout=20):
        assert isinstance(config, Config)

        self.config = config
        self.__mqtt_flag_dict = PahoMqttSessionFlags()
        logger = Logger(config.log_file, level=config.log_level)

        super(LLServer, self).__init__(config.i2tcp_psk, config.i2tcp_port,
                                       max_connections, logger, secured_connection,
                                       max_buffer_size, watchdog_timeout)
        self.__client = client.Client(self.config.mqtt_client_id)
        self.__client.username_pw_set(self.config.mqtt_user, self.config.mqtt_password)
        self.__client.on_connect = self.__onConnect
        self.__client.on_message = self.__onMessage

        self.__ll_clients = []

        self.connection_status = self.__mqtt_flag_dict[255]

        self.__flag_mqtt_loop_running = False

    def __onConnect(self, clt, userdata, flags, rc):
        self.connection_status = self.__mqtt_flag_dict[rc]
        if self.connection_status.is_connected:
            self.logger.INFO("[MQTT] successfully connected to host")
            for device in self.config:
                self.__ll_clients.append(LLMqttClient(self, device))
        else:
            self.logger.ERROR("[MQTT] failed to connect to MQTT server, {}, retrying".format(
                self.connection_status.status))

    def __onMessage(self, clt, userdata, message):
        self.logger.DEBUG("[MQTT] [receiver] received massage from topic \"{}\"".format(message.topic))
        for con in self.__ll_clients:
            assert isinstance(con, LLMqttClient)
            con.messageHandler(message)

    def __autoReconnectThread(self):
        self.threads.update({"mqttClientAutoReconnect": True})
        cnt = 50
        while self.live:
            if not self.__client.is_connected():
                cnt += 1
                time.sleep(0.1)

                if cnt > 50:
                    self.logger.INFO("[MQTT] connecting to MQTT server at {}:{}".format(
                        self.config.mqtt_host, self.config.mqtt_port))
                    try:
                        self.__client.connect(self.config.mqtt_host, self.config.mqtt_port)
                    except Exception as err:
                        self.logger.ERROR("[MQTT] failed to connect to MQTT server, {}, retrying in 5 seconds".format(
                            err))

                    cnt = 0

            try:
                self.__client.loop()
            except Exception as err:
                self.logger.ERROR("[MQTT] [loop] {}".format(err))

        self.threads.update({"mqttClientAutoReconnect": False})

    def start(self, port=None):
        super(LLServer, self).start(port)

        threading.Thread(target=self.__autoReconnectThread).start()

    def kill(self):
        super(LLServer, self).kill()

    def getMqttClient(self):
        return self.__client

    def getAllMqttRootTopics(self):
        ret = []
        for con in self.__ll_clients:
            assert isinstance(con, LLMqttClient)
            ret.append(con.topic_root)

    def getDeviceClient(self, root_topic):
        for con in self.__ll_clients:
            assert isinstance(con, LLMqttClient)
            if con.topic_root in root_topic:
                return con


if __name__ == '__main__':
    ll = LLServer(Config("sample/config.json"))
    ll.start()



    try:
        input("")
    except KeyboardInterrupt:
        pass
    ll.kill()
