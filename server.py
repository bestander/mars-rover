import asyncio
import json
import socket
import time
import imutils
import RPi.GPIO as GPIO
import threading
import cv2
from quart import Quart
from quart import render_template
from quart import websocket
from quart import Response
from evdev import InputDevice, categorize, ecodes, list_devices

MIME_TYPES = {
    "html": "text/html",
    "js": "text/javascript",
    "css": "text/css"
}
MAX_AXIS_VALUE = 32767
PORT = 8765

PWM_FREQUENCY = 50
STOP_DUTY_CYCLE = 7.5 # PWM value (7.5% of 20ms cycle) is between forward and backward, means stop
DUTY_CYCLE_RANGE = 2.5 # 7.5% - 10% means forward, 5% - 7.5% means backward

LEFT_SIDE_PIN = 35
RIGHT_SIDE_PIN = 33
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

GPIO.setup(LEFT_SIDE_PIN, GPIO.OUT)
left_pwm = GPIO.PWM(LEFT_SIDE_PIN, PWM_FREQUENCY)
left_pwm.start(0)
left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE)

GPIO.setup(RIGHT_SIDE_PIN, GPIO.OUT)
right_pwm = GPIO.PWM(RIGHT_SIDE_PIN, PWM_FREQUENCY)
right_pwm.start(0)
right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE)

app = Quart(__name__)

def test_run_motors():
    # init sequesnce
    left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE - DUTY_CYCLE_RANGE)
    right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE + DUTY_CYCLE_RANGE)
    time.sleep(3)
    left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE)
    right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE)

# run motors and delay to allow camera to init
test_run_motors()

def get_hostname():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    hostname = s.getsockname()[0]
    s.close()
    return hostname

@app.route("/")
async def index():
    # return the rendered template
    return await render_template("controls.html")

class Camera:
    last_frame = []

    def __init__(self, source: int):
        self.video_source = source
        self.cv2_cam = cv2.VideoCapture(self.video_source)
        self.event = asyncio.Event()

    def set_video_source(self, source):
        self.video_source = source
        self.cv2_cam = cv2.VideoCapture(self.video_source)

    async def get_frame(self):
        await self.event.wait()
        self.event.clear()
        return Camera.last_frame

    def frames(self):
        if not self.cv2_cam.isOpened():
            raise RuntimeError("Could not start camera.")

        while True:
            # read current frame
            _, frame = self.cv2_cam.read()

            # encode as a jpeg image and return it
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.GaussianBlur(frame, (7,7), 0)
            frame = cv2.Canny(frame, 50, 50)

            Camera.last_frame = [cv2.imencode(".jpg", frame)[1].tobytes(), frame]
            self.event.set()
            yield Camera.last_frame
        self.cv2_cam.release()

async def gen(c: Camera):
    for frame in c.frames():
        # d_frame = cv_processing.draw_debugs_jpegs(c.get_frame()[1])
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame[0] + b"\r\n")

c_gen = gen(Camera(0))

@app.route("/video_feed")
def video_feed():
    return Response(c_gen, mimetype="multipart/x-mixed-replace; boundary=frame")

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
            debounced.t = threading.Timer(wait, call_it)
            debounced.t.start()
        return debounced
    return decorator

@debounce(1)
def stop():
   print("stopping")
   left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE)
   right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE)

@app.websocket("/ws")
async def handle_websocket_commands():
    websocket.headers
    while True:
        try:
            message = await websocket.receive()
            data = json.loads(message)
            if data["action"] == "move":
                direction = data["direction"]
                print(f"< {direction}")
                if direction == "forward":
                    left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE - DUTY_CYCLE_RANGE)
                    right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE + DUTY_CYCLE_RANGE)
                elif direction == "backward":
                    left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE + DUTY_CYCLE_RANGE)
                    right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE - DUTY_CYCLE_RANGE)
                elif direction == "left":
                    left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE - DUTY_CYCLE_RANGE)
                    right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE - DUTY_CYCLE_RANGE)
                elif direction == "right":
                    left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE + DUTY_CYCLE_RANGE)
                    right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE + DUTY_CYCLE_RANGE)
                response = f"Ack {direction}!"
                await websocket.send(response)
                stop()
            else:
                print("unsupported event: {}", data)
                await websocket.send(f"Echo {data}")
        except asyncio.CancelledError:
            # Handle disconnect
            raise

async def wait_for_controller(loop):
    devices = [InputDevice(path) for path in list_devices()]
    controller = next((device for device in devices if device.name == "Wireless Steam Controller"), None)
    if controller == None:
        await asyncio.sleep(1)
        return (await wait_for_controller(loop))
    else:
        return await controller_event_hanlder(controller)

last_x_axis_value = 0
last_y_axis_value = 0

async def controller_event_hanlder(dev):
    global last_x_axis_value
    global last_y_axis_value

    async for event in dev.async_read_loop():
        if event.type == ecodes.EV_ABS:
            category = categorize(event)
            if (ecodes.ABS[event.code] == 'ABS_X'):
                last_x_axis_value = event.value
            if (ecodes.ABS[event.code] == 'ABS_Y'):
                last_y_axis_value = event.value
            
            if abs(last_x_axis_value) > abs(last_y_axis_value):
                # turn mode
                duty_cycle_change = DUTY_CYCLE_RANGE * last_x_axis_value / MAX_AXIS_VALUE
                left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE - duty_cycle_change)
                right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE - duty_cycle_change)

            else:
                # move mode
                duty_cycle_change = DUTY_CYCLE_RANGE * last_y_axis_value / MAX_AXIS_VALUE
                left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE + duty_cycle_change)
                right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE - duty_cycle_change)

if __name__ == "__main__":
    hostname = get_hostname()
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(wait_for_controller(loop))

        app.run(host = hostname, port = PORT)

        loop.run_forever()

    except KeyboardInterrupt:
        print("User Cancelled")

    finally:
        print("Cleaning")
        left_pwm.stop()
        right_pwm.stop()
        GPIO.cleanup()
        quit()
   