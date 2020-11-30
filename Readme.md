# Profanity Mars Rover

This is an R&D project of 3d printed rover powered by Raspberry Pi and controlled by either a camera over internet or a gamepad.
Video can be streamed via browser, analyzed on Raspberry Pi or remotely in the cloud.

## Body 3D prints 

Project is based on https://www.thingiverse.com/thing:1318414 (costs 10$ to obtain the STL files), the schematics and parts lists are incomplete, so it required some research to get all the parts together, I was able to obrain everything through Amazon and will list all the parts here later.

## Wire up

2BD: I'll post pictures here

## Code

Rover controls are written in Python 3, main components:
- USB reciever for gamepad controls (evdev package)
- Pi Camera (RTCBot package)
- Web server (aiohttp package) + React/WebRTC based client
- Motors controls (RPi.GPIO package)


### Quick Robot setup

- Install Raspbian
- Enable I2C and SSH
- sudo apt-get install python3-numpy python3-cffi python3-aiohttp \
    libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev \
    libswscale-dev libswresample-dev libavfilter-dev libopus-dev \
    libvpx-dev pkg-config libsrtp2-dev python3-opencv pulseaudio \ python3-rpi.gpio
- Install sound card https://wiki.seeedstudio.com/ReSpeaker_2_Mics_Pi_HAT/
- pip3 install -r robot-requirements.txt
- python3 robot.py
- Installing missing native .so files https://blog.piwheels.org/how-to-work-out-the-missing-dependencies-for-a-python-package/ (for cv2)

### Quick webserver setup

- pip3 install -r webserver-requirements.txt
- python3 web-server.py

## Autostart

```/lib/systemd/system/mars-rover.service
 [Unit]
 Description=Mars Rover Service
 After=multi-user.target

 [Service]
 Type=idle
 WorkingDirectory=/home/pi/mars-rover
 ExecStartPre=pulseaudio -D
 ExecStart=/usr/bin/python3 ./robot.py
 User=pi
 Restart=always

 [Install]
 WantedBy=multi-user.target
 ```

To test:
`sudo systemctl start mars-rover`

