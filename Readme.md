# Mars Rover


## Body 3D prints 


## Wire up



### Quick setup

- Install Raspbian
- Enable I2C and SSH
- sudo apt install python3-rpi.gpio
- python3 server.py

## Autostart

```/lib/systemd/system/mars-rover.service
[Unit]
 Description=Mars Rover Service
 After=multi-user.target

 [Service]
 Type=idle
 WorkingDirectory=/home/pi/mars-rover
 ExecStart=/usr/bin/python3 server.py > ./mars-rover.log 2>&1
 User=pi

 [Install]
 WantedBy=multi-user.target
 ```


