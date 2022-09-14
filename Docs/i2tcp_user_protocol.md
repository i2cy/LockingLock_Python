# Client

| CmdID | TopicRootofTargetDevice | Payload | Description                                  |
|-------|-------------------------|---------|----------------------------------------------|
| 0x01  | None                    | None    | get all of the root topics of devices        |
| 0x10  | str                     | None    | check if device is online                    |
| 0x11  | str                     | None    | get device storage json dict                 |
| 0x20  | str + ","               | json    | configurate device and update cloud storages |
| 0x21  | str                     | None    | requesting motor calibration                 |
| 0x22  | str                     | None    | requesting unlock                            |
| 0x23  | str                     | None    | ring device motor                            |


# Server

| CmdID | Payload   | Description                                    |
|-------|-----------|------------------------------------------------|
| 0x01  | uint8     | return flag                                    |
| 0xf1  | json      | list of all root topics                        |
| 0xe1  | json      | storage json dict of target device             |
| 0xd2  | uint8[16] | current dynamic password for offline unlocking |
