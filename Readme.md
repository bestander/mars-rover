# Mars Rover


## Body 3D prints 


## Wire up



## Docker
To achieve consistency across ultiple instances and to not rely in the bloat of the default 
Raspbian system this source code comes with docker file.

To get familiar with docker on Raspberry Pi check out [Hypriot blog](https://blog.hypriot.com/getting-started-with-docker-on-your-arm-device/).

The docker file builds all necessary libraries for GPIO and camera streamin from sources.

### Quick setup

```
docker run -it  -v /lib/modules:/lib/modules --restart unless-stopped --privileged bestander/mars-rover 

```

### Enable I2C

```
dtparam=i2c1=on

```

### Start the bot with docker

```
docker pull bestander/mars-rover
docker run -it  -v /lib/modules:/lib/modules --privileged bestander/mars-rover 
```

Pull mjpeg-streamer and start container that will stream video from camera via post 8080

```
docker pull bestander/mjpeg-streamer
docker run --device /dev/vchiq -p 8080:8080 -d bestander/mjpeg-streamer
```

Pull spy bot container that exposes web UI for controls
```
docker pull bestander/mars-rover
docker run -p 9000:80 -v /dev:/dev -d bestander/mars-rover
```

### Docker cheats

#### Useful articles for beginners:

https://www.digitalocean.com/community/tutorials/how-to-build-a-node-js-application-with-docker
https://www.balena.io/blog/building-arm-containers-on-any-x86-machine-even-dockerhub/


#### Automatic start on power on

Add `--restart unless-stopped` flag


#### Build container

```
docker build -t bestander/mars-rover .
```

#### Push new version

```
docker push bestander/mars-rover
```

#### Stop container

```
docker stop <name/hash>
```

#### To ssh to a running containers
```
docker ps
docker exec -it <name> /bin/bash
```

#### Run container without pushing it to background

Skip the `-d` option
```
docker run -it --privileged -v /dev:/dev negash/rpi-blaster
```

#### To clean space
```
docker images -a
docker system prune -a
```



