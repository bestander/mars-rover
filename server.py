
import os
import asyncio
import datetime
import random
import functools
import websockets
import json
import RPi.GPIO as GPIO

from http import HTTPStatus
from threading import Timer

MIME_TYPES = {
    "html": "text/html",
    "js": "text/javascript",
    "css": "text/css"
}

motor_pin = 32
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(motor_pin, GPIO.OUT)
pi_pwm = GPIO.PWM(motor_pin, 50)
pi_pwm.start(0)
pi_pwm.ChangeDutyCycle(7.5)

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

@debounce(1)
def stop():
   print("stopping")
   pi_pwm.ChangeDutyCycle(7.5)

async def handleCommands(websocket, path):
    async for message in websocket:
        data = json.loads(message)
        if data["action"] == "move":
            direction = data["direction"]
            pi_pwm.ChangeDutyCycle(9.5)
            print(f"< {direction}")
            response = f"Ack {direction}!"
            await websocket.send(response)
            stop()
        else:
            print("unsupported event: {}", data)

if __name__ == "__main__":
    # set first argument for the handler to current working directory
    handler = functools.partial(process_request, os.getcwd())
    start_server = websockets.serve(handleCommands, '127.0.0.1', 8765,
                                    process_request=handler)
    print("Running server at http://127.0.0.1:8765/")

    try:
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    except KeyboardInterrupt:
        print("User Cancelled")

    finally:
        print("Cleaning")
        pi_pwm.stop()
        GPIO.cleanup()
        quit()
   