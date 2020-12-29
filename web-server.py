from aiohttp import web
import datetime
from rtcbot import Websocket, getRTCBotJS

routes = web.RouteTableDef()


@routes.get("/")
async def index(request):
    return web.FileResponse('static/index.html')


@routes.get("/rtcbot.js")
async def rtcbotjs(request):
    return web.Response(content_type="application/javascript", text=getRTCBotJS())

robotWebSocket = None  # Websocket connection to the robot


@routes.get("/registerRobot")
async def websocket(request):
    global robotWebSocket
    if robotWebSocket is not None:
        c = robotWebSocket.close()
        if c is not None:
            await c
        
    robotWebSocket = Websocket(request)
    print("{:%Y-%m-%d %H:%M:%S}: Robot Connected".format(datetime.datetime.now()))
    await robotWebSocket  # Wait until the websocket closes
    print("{:%Y-%m-%d %H:%M:%S}: Robot Disconnected".format(datetime.datetime.now()))


@routes.post("/negotiateRtcConnectionWithRobot")
async def connect(request):
    global robotWebSocket
    if robotWebSocket is None:
        raise web.HTTPInternalServerError("There is no robot connected")
    clientOffer = await request.json()
    # Send the offer to the robot, and receive its response
    robotWebSocket.put_nowait(clientOffer)
    robotResponse = await robotWebSocket.get()
    return web.json_response(robotResponse)


async def cleanup(app=None):
    global robotWebSocket
    if robotWebSocket is not None:
        c = robotWebSocket.close()
        if c is not None:
            await c

app = web.Application()
app.router.add_static('/static', './static')
app.add_routes(routes)
app.on_shutdown.append(cleanup)

web.run_app(app, port=8080)
