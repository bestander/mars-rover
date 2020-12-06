import asyncio
import cv2
from evdev import InputDevice, categorize, ecodes, list_devices
import json
import random
from rtcbot import RTCConnection, getRTCBotJS, PiCamera, Websocket
import RPi.GPIO as GPIO
import numpy

REMOTE_WEB_SERVER = 'http://profanity-rover.space'
MAX_AXIS_VALUE = 32767
PWM_FREQUENCY = 50
# PWM value (7.5% of 20ms cycle) is between forward and backward, means stop
STOP_DUTY_CYCLE = 7.5
DUTY_CYCLE_RANGE = 2.5  # 7.5% - 10% means forward, 5% - 7.5% means backward

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

camera = PiCamera()
bwSubscription = asyncio.Queue()

frames = 0
hsv = None
red = {"hueMin": 0, "hueMax": 10, "satMin": 0, "satMax": 10, "valMin": 15, "valMax":60}
MIN_PIXELS_THRESHOLD = 2000

@camera.subscribe
async def onFrame(frame):
    global frames
    global hsv
    global red
    frames = frames + 1
    if frames % 5 == 0:
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # frame = cv2.GaussianBlur(frame, (3, 3), 0)
        # frame = cv2.Canny(frame, 50, 50)
        # frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        if hsv == None:
            hsv = red
        lowerHsvRange = numpy.array([hsv["hueMin"], hsv["satMin"], hsv["valMin"]])
        upperHsvRange = numpy.array([hsv["hueMax"], hsv["satMax"], hsv["valMax"]])
        mask = cv2.inRange(frame, lowerHsvRange, upperHsvRange)
        # Crop left and right half of mask
        x, y, w, h = 0, 0, frame.shape[1]//2, frame.shape[0]
        left = mask[y:y+h, x:x+w]
        right = mask[y:y+h, x+w:x+w+w]
        # Count pixels
        left_pixels = cv2.countNonZero(left)
        right_pixels = cv2.countNonZero(right)
        print(left_pixels, right_pixels)
        if left_pixels - right_pixels > MIN_PIXELS_THRESHOLD:
            left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE - DUTY_CYCLE_RANGE)
            right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE + DUTY_CYCLE_RANGE)
        elif right_pixels - left_pixels > MIN_PIXELS_THRESHOLD:
            left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE + DUTY_CYCLE_RANGE)
            right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE - DUTY_CYCLE_RANGE)
        elif left_pixels + right_pixels > MIN_PIXELS_THRESHOLD:
            left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE + DUTY_CYCLE_RANGE)
            right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE + DUTY_CYCLE_RANGE)
        else:
            left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE)
            right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE)
        frames = 0
        frame = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        await bwSubscription.put(frame)

connections = []


async def registerOnServerAndAwaitRtcConnections():
    print("sending /registerRobot")
    ws = Websocket(REMOTE_WEB_SERVER + '/registerRobot')
    while True:
        remoteDescription = await ws.get()
        print("new web user requested connect")
        connection = RTCConnection()
        connection.video.putSubscription(bwSubscription)
        connection.subscribe(onMessage)
        @connection.onClose
        def close():
            print("Connection Closed")
            connections.remove(connection)

        connections.append(connection)
        robotDescription = await connection.getLocalDescription(remoteDescription)
        ws.put_nowait(robotDescription)


async def onMessage(data):
    global hsv
    if data["action"] == "move":
        direction = data["direction"]
        if direction == "forward":
            left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE + DUTY_CYCLE_RANGE)
            right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE + DUTY_CYCLE_RANGE)
        elif direction == "backward":
            left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE - DUTY_CYCLE_RANGE)
            right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE - DUTY_CYCLE_RANGE)
        elif direction == "left":
            left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE - DUTY_CYCLE_RANGE)
            right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE + DUTY_CYCLE_RANGE)
        elif direction == "right":
            left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE + DUTY_CYCLE_RANGE)
            right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE - DUTY_CYCLE_RANGE)
        elif direction == "stop":
            left_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE)
            right_pwm.ChangeDutyCycle(STOP_DUTY_CYCLE)
    elif data["action"] == "hsv":
        hsv = data["hsv"]
    else:
        print("unsupported event: {}", data)


async def waitForController():
    devices = [InputDevice(path) for path in list_devices()]
    controller = next((device for device in devices if device.name ==
                       "Wireless Steam Controller"), None)
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
        if event.type == ecodes.EV_ABS:
            if (ecodes.ABS[event.code] == 'ABS_X'):
                last_x_axis_value = event.value
            if (ecodes.ABS[event.code] == 'ABS_Y'):
                last_y_axis_value = event.value

            if abs(last_x_axis_value) > abs(last_y_axis_value):
                # turn mode
                left_pwm.ChangeDutyCycle(
                    STOP_DUTY_CYCLE + DUTY_CYCLE_RANGE * last_x_axis_value / MAX_AXIS_VALUE)
                right_pwm.ChangeDutyCycle(
                    STOP_DUTY_CYCLE - DUTY_CYCLE_RANGE * last_x_axis_value / MAX_AXIS_VALUE)
            else:
                # drive mode
                left_adjustment = 1
                right_adjustment = 1
                if last_x_axis_value > 0:
                    left_adjustment = (
                        1 - abs(last_x_axis_value) / MAX_AXIS_VALUE)
                else:
                    right_adjustment = (
                        1 - abs(last_x_axis_value) / MAX_AXIS_VALUE)

                right_duty_cycle = STOP_DUTY_CYCLE - DUTY_CYCLE_RANGE * \
                    last_y_axis_value / MAX_AXIS_VALUE * left_adjustment
                left_duty_cycle = STOP_DUTY_CYCLE - DUTY_CYCLE_RANGE * \
                    last_y_axis_value / MAX_AXIS_VALUE * right_adjustment
                left_pwm.ChangeDutyCycle(left_duty_cycle)
                right_pwm.ChangeDutyCycle(right_duty_cycle)
        elif event.type == ecodes.EV_KEY and event.value == 1:
            # steam controller button presses
            if str(event.code) in STEAM_CONTROLLER_CODES_TO_SOUNDS:
                asyncio.get_event_loop().create_task(playSound(str(event.code)))
                

SOUNDBAR_PATH = 'soundboard'
STEAM_CONTROLLER_CODES_TO_SOUNDS = {
    '304': SOUNDBAR_PATH + '/amer-neverfall.mp3',
    '305': SOUNDBAR_PATH + '/comm-death.mp3',
    '307': SOUNDBAR_PATH + '/comm-detect.mp3',
    '308': SOUNDBAR_PATH + '/comm-failure.mp3',
    '310': SOUNDBAR_PATH + '/comm-targacq.mp3',
    '311': SOUNDBAR_PATH + '/compos.mp3',
    '312': SOUNDBAR_PATH + '/compos-2.mp3',
    '313': SOUNDBAR_PATH + '/compos-4.mp3',
    '314': SOUNDBAR_PATH + '/comm-setback.mp3',
    '315': SOUNDBAR_PATH + '/libonline-1.mp3',
    '318': SOUNDBAR_PATH + '/freedom.mp3',
    '336': SOUNDBAR_PATH + '/warning-1.mp3',
    '337': SOUNDBAR_PATH + '/primtargets-4.mp3',
    '544': SOUNDBAR_PATH + '/death-comm.mp3',
    '545': SOUNDBAR_PATH + '/death-nonneg.mp3',
    '546': SOUNDBAR_PATH + '/destroy-comm.mp3',
    '547': SOUNDBAR_PATH + '/embrace-dem.mp3',
    'DEATH-1': SOUNDBAR_PATH + '/death-1.mp3',
    'DEATH-2': SOUNDBAR_PATH + '/death-3.mp3',
    'OVERCHARGE': SOUNDBAR_PATH + '/overcharge.mp3',
    'SELF-DESTRUCT': SOUNDBAR_PATH + '/primtargets-3.mp3',
}


playing = False
async def playSound(key):
    global playing
    if playing == False:
        playing = True
        proc = await asyncio.create_subprocess_exec(
        'mpg123', STEAM_CONTROLLER_CODES_TO_SOUNDS[key],
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        playing = False


loop = asyncio.get_event_loop()
loop.create_task(waitForController())
loop.create_task(playSound(random.choice(list(STEAM_CONTROLLER_CODES_TO_SOUNDS.keys()))))
asyncio.ensure_future(registerOnServerAndAwaitRtcConnections())
try:
    loop.run_forever()
finally:
    camera.close()
    for conn in connections:
        conn.close()

