# ESP32S3 LockingLock Server

This repo is the server part of LockingLock project.

[Github Link](https://github.com/i2cy/LockingLock_Python)

# Installation
`pip install i2llserver`

# Setup
`i2llsrv setup`

This command will help you to edit a configuration file and 
add startup scripts on boot in systemd

# Auto-Startup on Linux
By running `i2llsrv setup` command, setup wizard will ask you in the end
of setup sequence for choosing whether should it register a systemd 
service. Choose yes to generate service file and register which requires
root permission or sudo permission.

However, if the setup wizard failed to register startup service, it will generate
a one-script-done shell script at your home directory which named as:

`enable_auto-startup_for_i2ll.sh`

By executing this shell scripts by root or sudo, the automatic startup
service will be registered which named as `i2llserver.service`

Use `service i2llserver start|stop|restart` to control server
