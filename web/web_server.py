import datetime
import random

import websockets
from websockets.server import WebSocketServer
import asyncio
import utils


class OhminatorWebServer():
    def __init__(self, client):
        self.client = client
        self.connected = set()

    async def handler(self, websocket, path):
        # Register.
        self.connected.add(websocket)
        try:
            # Implement logic here.
            await asyncio.wait([ws.send("Hello!") for ws in self.connected])
            await asyncio.sleep(10)
        finally:
            # Unregister.
            self.connected.remove(websocket)

    async def message_handler(self, websocket, path):
        while True:
            response = await websocket.revc()
            if response == "get_servers_info":
                await self.get_servers_info(websocket, path)
            elif response == "get_servers":
                await self.get_servers(websocket, path)

    async def get_servers_info(self, websocket, path):
        servers = sum(1 for _ in self.client.servers)
        users = sum(1 for _ in self.client.get_all_members())
        response = "Ohminator is currently serving {} server{}, {} user{}.".format(
            servers, "s" if servers != 1 else "", users, "s" if users != 1 else "")
        await websocket.send(response)

    async def get_servers(self, websocket, path):
        server_list = utils.server_list
        await websocket.send(map(lambda server: server.name, server_list))

    def setup_server(self, loop=None):
        start_server = websockets.serve(self.message_handler, '127.0.0.1', 5678)
        if not loop:
            loop = asyncio.get_event_loop()
        print("Starting web socket!")
        loop.create_task(start_server)
