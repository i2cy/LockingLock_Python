#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: ESP32S3LockingLock
# Filename: set_wifi
# Created on: 2022/7/12
from i2cylib.serial import getComDevice
from i2cylib.serial import HTSocket
import time
import threading

COM = getComDevice(("CH340", "CH9102"))[0]

SSID = "AMA_CDUT"
PWD = "12356789"
MQTT_USER = "icy"
MQTT_PWD = "__C4o0d9y6#"

BR = 921600

LIVE = True


def minicom_thread(clt):
    assert isinstance(clt, HTSocket)
    while LIVE:
        try:
            print(clt.client.read(1).decode("utf-8"), end="")
        except:
            continue


def main():
    global LIVE, COM
    inputs = input("Input COM port for communication (default {}): ".format(COM))
    if inputs:
        COM = inputs
    clt = HTSocket(COM, BR)
    clt.connect()
    threading.Thread(target=minicom_thread, args=(clt,)).start()

    while True:
        try:
            input("[Press ENTER to configure]")

            print("sending ssid...")
            clt.send(b"\xcb\xcd", b"\x10" + SSID.encode() + b"\x00")

            time.sleep(0.5)

            print("sending password...")
            clt.send(b"\xcb\xcd", b"\x11" + PWD.encode() + b"\x00")

            time.sleep(0.5)

            print("requesting connect...")
            clt.send(b"\xcb\xcd", b"\x12")

            print("sending mqtt username...")
            clt.send(b"\xcb\xcd", b"\x13" + MQTT_USER.encode() + b"\x00")

            time.sleep(0.5)

            print("sending mqtt password...")
            clt.send(b"\xcb\xcd", b"\x14" + MQTT_PWD.encode() + b"\x00")

            time.sleep(0.5)

        except KeyboardInterrupt:
            break

    LIVE = False
    time.sleep(0.5)
    clt.close()


if __name__ == '__main__':
    main()
