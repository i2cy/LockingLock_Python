#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: ESP32S3LockingLock
# Filename: mpu6050
# Created on: 2022/6/28

import serial
import time
import matplotlib.pyplot as plt

COM = "COM13"
BR = 115200

RECORD_FILE = "gyro_test3.csv"


def main():
    clt = serial.Serial(COM, BR)
    f = open(RECORD_FILE, "wb")

    for i in range(200):
        data = clt.readline()

    print("Recording...")
    t0 = time.time()
    i = 0
    while True:
        try:
            t1 = time.time()
            data = clt.readline()
            data = "{:.4f},".format(t1 - t0).encode() + data
            i += 1
            if i >= 100:
                fps = time.time() - t1
                if fps > 0:
                    print("FPS: {:.2f}".format(1 / fps))
                i = 0
            f.write(data)
        except KeyboardInterrupt:
            break
    print("Stopped")

    f.close()
    clt.close()

    f = open(RECORD_FILE, "r")
    x = []
    y1 = []
    y2 = []
    y3 = []
    lpf1 = 0
    lpf2 = 0

    first_line = True
    for line in f:
        if line:
            raw = line.split(",")
            try:
                if first_line:
                    x.append(float(raw[0]))
                    lpf1 = lpf2 = int(raw[3])
                    first_line = False
                    data_raw = int(raw[3])
                    y1.append(data_raw)
                    y2.append(lpf1)
                    y3.append(lpf2)
                else:
                    x.append(float(raw[0]))
                    data_raw = int(raw[3])
                    lpf1 += 0.3 * (data_raw - lpf1)
                    lpf2 += 0.3 * (lpf1 - lpf2)
                    y1.append(data_raw)
                    y2.append(lpf1)
                    y3.append(lpf2)
            except:
                continue

    plt.plot(x, y1, "green", alpha=0.5)
    plt.plot(x, y2, "blue", alpha=0.8)
    plt.plot(x, y3, "red")

    x_major_locator = plt.MultipleLocator(1)
    ax = plt.gca()
    ax.xaxis.set_major_locator(x_major_locator)
    plt.xlim(-0.1 * x[-1], x[-1] + 0.1 * x[-1])

    plt.show()


if __name__ == '__main__':
    main()
