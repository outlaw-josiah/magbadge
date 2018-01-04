import asyncio
import websockets
{"action":"echo", "params":1}

async def sendrecv(port = 28424):
	try:
		async with websockets.connect('ws://localhost:' + str(port)) as websocket:
			name = ""
			while name.upper() != "STOP":
				name = input("DATA> ")
				await websocket.send(name)
				greeting = await websocket.recv()
				print("RESP> {}".format(greeting))
	except KeyboardInterrupt:
		print("\nStopping sendrecv()")
	except websockets.exceptions.ConnectionClosed:
		print("Server closed connection")

async def hello():
	async with websockets.connect('ws://localhost:28424') as websocket:
		name = input("DATA> ")
		await websocket.send(name)
		print("> {}".format(name))
		greeting = await websocket.recv()
		print("< {}".format(greeting))

async def getmany(start=0, stop=1, meal="undefined", ratelimit=True):
	async with websockets.connect('ws://localhost:28424') as websocket:
		for x in range(start, stop):
			if not ((x - start) % 100):
				print(x)
			await websocket.send(
				'{{"action":"query.badge","params":{},'
				'"meal":"{}"}}'.format(x, meal))
			await websocket.recv()
			if ratelimit:
				await asyncio.sleep(0.1)

def run(func, *args, **kwargs):
	asyncio.get_event_loop().run_until_complete(func(*args, **kwargs))

