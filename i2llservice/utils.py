#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: ESP32S3LockingLock
# Filename: utils
# Created on: 2022/10/10


def dyn16ToDec(data: bytes, length: int = 4) -> list:
    """
    convert bytes of DynKey16 to decimal digests
    :param data: bytes of DynKey16
    :param length: int
    :return: list of decimal digit
    """
    ret = [int(ele / 25.6) + 1 for ele in data[:length]]

    return ret


if __name__ == '__main__':
    from i2cylib.crypto.keygen import DynKey16
    from i2cylib.utils.bytes import random_keygen
    psk = random_keygen(8)
    kg = DynKey16(psk)
    dat = kg.keygen()
    print("random PSK generated: {}".format(psk.hex()))
    print("generated dyn16: {}".format(dat.hex()))
    print("converted: {}".format(dyn16ToDec(dat)))
