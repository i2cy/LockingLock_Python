#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: ESP32S3LockingLock
# Filename: dynkey_test
# Created on: 2022/8/21


from i2cylib.crypto import DynKey16
from i2cylib.serial import HTSocket
from i2cylib.serial import getComDevice
import time


COM = getComDevice(("CH340", "CH9102"))[0]
BR = 921600
ADDR = b"\xcb\x02"
DPSK = b"testtest123"


def main():
    dk = DynKey16(DPSK)
    clt = HTSocket(COM, BR, timeout=60)
    clt.connect()

    while True:
        data = clt.recv(ADDR)
        key = data[:64]
        ts = data[64:]
        ts = int().from_bytes(ts, "big", signed=False)
        if data:
            break

    print("received TS: {}, key: {}".format(ts, key))
    print("current TS: {}, key: {}".format(), dk.keygen())


if __name__ == '__main__':
    main()
