from aiohttp import web
from rtcbot import Websocket, getRTCBotJS

routes = web.RouteTableDef()


@routes.get("/")
async def index(request):
    return web.FileResponse('static/index.html')


@routes.get("/rtcbot.js")
async def rtcbotjs(request):
    return web.Response(content_type="application/javascript", text=getRTCBotJS())

ws = None  # Websocket connection to the robot


@routes.get("/ws")
async def websocket(request):
    global ws
    if ws is not None:
        c = ws.close()
        if c is not None:
            await c
        
    ws = Websocket(request)
    print("Robot Connected")
    await ws  # Wait until the websocket closes
    print("Robot disconnected")
    return ws.ws


@routes.post("/connect")
async def connect(request):
    global ws
    if ws is None:
        raise web.HTTPInternalServerError("There is no robot connected")
    clientOffer = await request.json()
    # Send the offer to the robot, and receive its response
    ws.put_nowait(clientOffer)
    robotResponse = await ws.get()
    return web.json_response(robotResponse)


async def cleanup(app=None):
    global ws
    if ws is not None:
        c = ws.close()
        if c is not None:
            await c

app = web.Application()
app.router.add_static('/static', './static')
app.add_routes(routes)
app.on_shutdown.append(cleanup)

web.run_app(app, port=8000)
