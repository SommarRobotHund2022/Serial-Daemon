# Serial-Daemon

Daemon that facilitates serial communication between the Raspberry Pi and OpenCat running on the robotdogs Arduino / NyBoard.
All incomming data in published on a ZMQ PUB socket on port 2271.
To write data to serial, send the data to the ZMQ REQ socket on port 2272

## Installation (systemd)
### Manual
```
$ sudo git clone https://github.com/SommarRobotHund2022/Serial-Daemon.git
$ cd Serial-Daemon
$ sudo cp serial-daemon.service /etc/systemd/system/
$ sudo systemctl enable serial-daemon
$ sudo systemctl start serial-daemon
```
### Auto
```
$ sudo git clone https://github.com/SommarRobotHund2022/Serial-Daemon.git
$ cd Serial-Daemon
$ chmod +x install.sh
$ sudo ./install.sh
```

## Flags for running
* -d or --debug       - Print debug info
* -q or --quiet       - Mute most printing
* -e or --echo        - Print what is received
* -i or --interactive - Write data to serial in the terminal
* --no-net            - Run without ZMQ sockets
* --port **\<PORT\>**     - Specify which serial port to use, default is **/dev/ttyS0**
