import asyncio
import websockets

async def test():
    try:
        async with websockets.connect('ws://127.0.0.1:8000/api/v1/ws/stream') as ws:
            print('Connected!')
            await ws.send('{"action": "subscribe", "topic": "system"}')
            res = await ws.recv()
            print('Received:', res)
    except Exception as e:
        print('Error:', e)

asyncio.run(test())
