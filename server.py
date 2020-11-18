
import os
import asyncio
import datetime
import random
import functools
import websockets
import json
import socket
import time
import RPi.GPIO as GPIO

from evdev import InputDevice, categorize, ecodes, list_devices
from http import HTTPStatus
from threading import Timer


LEFT_FORWARD = 4.5
LEFT_BACK = 9.5
RIGHT_FORWARD = 9.5
RIGHT_BACK = 4.5
STOP = 7.5

MIME_TYPES = {
    "html": "text/html",
    "js": "text/javascript",
    "css": "text/css"
}

left_side_pin = 35
right_side_pin = 33
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

GPIO.setup(left_side_pin, GPIO.OUT)
left_pwm = GPIO.PWM(left_side_pin, 50)
left_pwm.start(0)
left_pwm.ChangeDutyCycle(STOP)

GPIO.setup(right_side_pin, GPIO.OUT)
right_pwm = GPIO.PWM(right_side_pin, 50)
right_pwm.start(0)
right_pwm.ChangeDutyCycle(STOP)

time.sleep(3)
## init sequesnce
left_pwm.ChangeDutyCycle(LEFT_FORWARD)
right_pwm.ChangeDutyCycle(RIGHT_FORWARD)
time.sleep(3)
left_pwm.ChangeDutyCycle(STOP)
right_pwm.ChangeDutyCycle(STOP)

def get_hostname():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    hostname = s.getsockname()[0]
    s.close()
    return hostname

async def process_request(sever_root, path, request_headers):
    """Serves a file when doing a GET request with a valid path."""

    if "Upgrade" in request_headers:
        return  # Probably a WebSocket connection

    if path == '/':
        path = '/index.html'

    response_headers = [
        ('Server', 'asyncio websocket server'),
        ('Connection', 'close'),
    ]

    # Derive full system path
    full_path = os.path.realpath(os.path.join(sever_root, path[1:]))

    # Validate the path
    if os.path.commonpath((sever_root, full_path)) != sever_root or \
            not os.path.exists(full_path) or not os.path.isfile(full_path):
        print("HTTP GET {} 404 NOT FOUND".format(path))
        return HTTPStatus.NOT_FOUND, [], b'404 NOT FOUND'

    # Guess file content type
    extension = full_path.split(".")[-1]
    mime_type = MIME_TYPES.get(extension, "application/octet-stream")
    response_headers.append(('Content-Type', mime_type))

    # Read the whole file into memory and send it out
    body = open(full_path, 'rb').read()
    response_headers.append(('Content-Length', str(len(body))))
    print("HTTP GET {} 200 OK".format(path))
    return HTTPStatus.OK, response_headers, body

def debounce(wait):
    """ Decorator that will postpone a functions
        execution until after wait seconds
        have elapsed since the last time it was invoked. """
    def decorator(fn):
        def debounced(*args, **kwargs):
            def call_it():
                fn(*args, **kwargs)
            try:
                debounced.t.cancel()
            except(AttributeError):
                pass
            debounced.t = Timer(wait, call_it)
            debounced.t.start()
        return debounced
    return decorator

@debounce(1)
def stop():
   print("stopping")
   left_pwm.ChangeDutyCycle(STOP)
   right_pwm.ChangeDutyCycle(STOP)

async def handle_websocket_commands(websocket, path):
    async for message in websocket:
        data = json.loads(message)
        if data["action"] == "move":
            direction = data["direction"]
            print(f"< {direction}")
            if direction == "forward":
                left_pwm.ChangeDutyCycle(LEFT_FORWARD)
                right_pwm.ChangeDutyCycle(RIGHT_FORWARD)
            elif direction == "backward":
                left_pwm.ChangeDutyCycle(LEFT_BACK)
                right_pwm.ChangeDutyCycle(RIGHT_BACK)
            elif direction == "left":
                left_pwm.ChangeDutyCycle(LEFT_BACK)
                right_pwm.ChangeDutyCycle(RIGHT_FORWARD)
            elif direction == "right":
                left_pwm.ChangeDutyCycle(LEFT_FORWARD)
                right_pwm.ChangeDutyCycle(RIGHT_BACK)

            response = f"Ack {direction}!"
            await websocket.send(response)
            stop()
        else:
            print("unsupported event: {}", data)

async def wait_for_controller(loop):
    devices = [InputDevice(path) for path in list_devices()]
    controller = next((device for device in devices if device.name == "Wireless Steam Controller"), None)
    if controller == None:
        await asyncio.sleep(1)
        return (await wait_for_controller(loop))
    else:
        return await controller_event_hanlder(controller)

    
async def controller_event_hanlder(dev):
    async for event in dev.async_read_loop():
        if event.type == ecodes.EV_ABS:
            category = categorize(event)
            if (ecodes.ABS[event.code] == 'ABS_X'):
                if event.value < 0:
                    left_pwm.ChangeDutyCycle(LEFT_FORWARD)
                    right_pwm.ChangeDutyCycle(RIGHT_BACK)
                elif event.value > 0:
                    left_pwm.ChangeDutyCycle(LEFT_BACK)
                    right_pwm.ChangeDutyCycle(RIGHT_FORWARD)
                else:
                    left_pwm.ChangeDutyCycle(STOP)
                    right_pwm.ChangeDutyCycle(STOP)
            if (ecodes.ABS[event.code] == 'ABS_Y'):
                if event.value < 0:
                    left_pwm.ChangeDutyCycle(LEFT_BACK)
                    right_pwm.ChangeDutyCycle(RIGHT_BACK)
                elif event.value > 0:
                    left_pwm.ChangeDutyCycle(LEFT_FORWARD)
                    right_pwm.ChangeDutyCycle(RIGHT_FORWARD)
                else:
                    left_pwm.ChangeDutyCycle(STOP)
                    right_pwm.ChangeDutyCycle(STOP)

if __name__ == "__main__":
    # set first argument for the handler to current working directory
    handler = functools.partial(process_request, os.getcwd())
    start_server = websockets.serve(handle_websocket_commands, None, 8765,
                                    process_request=handler)
    print("Running server at http://{}:8765/".format(get_hostname()))

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_server)
        loop.run_until_complete(wait_for_controller(loop))
        loop.run_forever()

    except KeyboardInterrupt:
        print("User Cancelled")

    finally:
        print("Cleaning")
        left_pwm.stop()
        right_pwm.stop()
        GPIO.cleanup()
        quit()
   