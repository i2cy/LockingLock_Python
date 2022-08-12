#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: ESP32S3LockingLock
# Filename: mpu6050
# Created on: 2022/6/28

import time
import struct
import matplotlib.pyplot as plt
from i2cylib.serial import HTSocket

COM = "COM13"
BR = 921600
ADDR = b"\xcb\x01"

TITLES = ["Acc X", "Acc Y", "Acc Z", "Gyro X", "Gyro Y", "Gyro Z"]
RECORD_FILE = "gyro_test.dat"


def main():
    clt = HTSocket(COM, BR)
    clt.connect()
    f = open(RECORD_FILE, "wb")

    for i in range(200):
        data = clt.client.read()

    print("Recording...")
    t0 = time.time()
    i = 0
    t2 = 0
    t1 = 0
    total_samples = 0
    while True:
        try:
            t1 = time.time()
            if not t2 and i < 100:
                t2 = t1
            data = clt.recv(ADDR)
            data = struct.pack("f", t1 - t0) + data
            i += 1
            if i >= 100:
                fps = time.time() - t2
                if fps > 0:
                    print("FPS: {:.2f}".format(100 / fps))
                i = 0
                t2 = 0
            f.write(data)
            total_samples += 1
        except KeyboardInterrupt:
            break
    print("Stopped")
    print("{:.2f}s of {} samples recorded".format(t1 - t0, total_samples))

    f.close()
    clt.close()

    index = 0

    for num in range(1, 8):
        f = open(RECORD_FILE, "rb")
        x = []
        y1 = []
        y2 = []
        y3 = []
        lpf1 = 0
        lpf2 = 0

        if num == 4:
            continue

        index += 1
        first_line = True
        last_x = 0
        current_x = 0
        while True:
            line = f.read(18)
            if line:
                raw = struct.unpack("fhhhhhhh", line)
                raw = [abs(val) for val in raw]
                try:
                    if first_line:
                        if last_x == float(raw[0]):
                            current_x = float(raw[0]) + 0.0005
                        x.append(current_x)
                        last_x = current_x
                        lpf1 = lpf2 = int(raw[num])
                        first_line = False
                        data_raw = int(raw[num])
                        y1.append(data_raw)
                        y2.append(lpf1)
                        y3.append(lpf2)
                    else:
                        x.append(float(raw[0]))
                        data_raw = int(raw[num])
                        lpf1 += 0.3 * (data_raw - lpf1)
                        lpf2 += 0.3 * (lpf1 - lpf2)
                        y1.append(data_raw)
                        y2.append(lpf1)
                        y3.append(lpf2)
                except:
                    continue
            else:
                break

        plt.subplot(230 + index)
        plt.title(TITLES[index - 1])
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
