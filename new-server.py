from aiohttp import web
import asyncio
import cv2
from evdev import InputDevice, categorize, ecodes, list_devices
import json
from rtcbot import RTCConnection, getRTCBotJS, PiCamera
import RPi.GPIO as GPIO
import threading


MAX_AXIS_VALUE = 32767
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

routes = web.RouteTableDef()
camera = PiCamera()
bwSubscription = asyncio.Queue()

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


frames = 0
@camera.subscribe
async def onFrame(frame):
    global frames
    frames = frames + 1
    if frames % 5 == 0:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.GaussianBlur(frame, (7,7), 0)
        frame = cv2.Canny(frame, 50, 50)
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        await bwSubscription.put(frame)

@routes.get("/")
async def index(request):
    return web.FileResponse('index.html')

@routes.get("/rtcbot.js")
async def rtcbotjs(request):
    return web.Response(content_type="application/javascript", text=getRTCBotJS())

# This sets up the connection
@routes.post("/connect")
async def connect(request):
    clientOffer = await request.json()
    conn = RTCConnection()
    conn.video.putSubscription(bwSubscription)
    serverResponse = await conn.getLocalDescription(clientOffer)
    conn.subscribe(onMessage)
    return web.json_response(serverResponse)
    

@debounce(1)
def stop():
   print("stopping")
   left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE)
   right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE)

async def onMessage(data):

    if data["action"] == "move":
        direction = data["direction"]
        print(f"< {direction}")
        if direction == "forward":
            left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE + DUTY_CYCLE_RANGE)
            right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE + DUTY_CYCLE_RANGE)
        elif direction == "backward":
            left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE - DUTY_CYCLE_RANGE)
            right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE - DUTY_CYCLE_RANGE)
        elif direction == "left":
            left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE + DUTY_CYCLE_RANGE)
            right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE - DUTY_CYCLE_RANGE)
        elif direction == "right":
            left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE - DUTY_CYCLE_RANGE)
            right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE + DUTY_CYCLE_RANGE)
        stop()
    else:
        print("unsupported event: {}", data)

async def cleanup(app):
    # TODO close all connections gracefully?
    camera.close()

app = web.Application()
app.router.add_static('/static', './static')
app.add_routes(routes)
app.on_shutdown.append(cleanup)

async def waitForController():
    print("waitForController")
    devices = [InputDevice(path) for path in list_devices()]
    controller = next((device for device in devices if device.name == "Wireless Steam Controller"), None)
    if controller == None:
        await asyncio.sleep(1)
        return (await waitForController())
    else:
        return await onControllerEvent(controller)

last_x_axis_value = 0
last_y_axis_value = 0

async def onControllerEvent(dev):
    global last_x_axis_value
    global last_y_axis_value

    async for event in dev.async_read_loop():
        print("onControllerEvent")

loop = asyncio.get_event_loop()
# loop.create_task(waitForController())
web.run_app(app, port = 8000)
