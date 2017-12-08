import datetime
import random

import websockets
from websockets.server import WebSocketServer
import asyncio
import utils


class OhminatorWebServer():
    def __init__(self, client):
        self.client = client

    async def get_servers(self, websocket, path):
        while True:
            servers = sum(1 for _ in self.client.servers)
            users = sum(1 for _ in self.client.get_all_members())
            response = "Ohminator is currently serving {} server{}, {} user{}.".format(
                servers, "s" if servers != 1 else "", users, "s" if users != 1 else "")
            await websocket.send(response)
            await asyncio.sleep(5)

    def setup_server(self, loop=None):
        start_server = websockets.serve(self.get_servers, '127.0.0.1', 5678)
        if not loop:
            loop = asyncio.get_event_loop()
        loop.run_until_complete(start_server)
