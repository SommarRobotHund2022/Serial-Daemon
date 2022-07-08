#!/usr/bin/bash

sudo cp serial-daemon.service /etc/systemd/system/

sudo systemctl enable serial-daemon
sudo systemctl start serial-daemon