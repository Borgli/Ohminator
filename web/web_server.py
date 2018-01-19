import datetime
import random
import traceback
from collections import OrderedDict

import websockets
from websockets.server import WebSocketServer
import asyncio
import utils
import json
import discord.utils


def generate_error(type, message):
    return json.loads({"type": type, "message": message})


def generate_server_json(server):
    roles = list(
        map(lambda role: {"name": role.name, "colour": role.colour.value, "permissions": role.permissions.value},
            server.roles))
    members = list(map(lambda member: {
        "name": member.name, "id": member.id, "bot": member.bot, "avatar_url": member.avatar_url,
        "default_avatar_url": member.default_avatar_url, "created_at": str(member.created_at),
        "display_name": member.display_name, "joined_at": str(member.joined_at), "status": str(member.status),
        "game": None if not member.game else {"name": member.game.name, "url": member.game.url},
        "colour": member.colour.value, "top_role": {"name": member.top_role.name, "id": member.top_role.colour.value,
                                                    "permissions": member.top_role.permissions.value}
    }, server.members))
    channels = list(map(lambda channel: {
        "name": channel.name, "id": channel.id, "topic": channel.topic, "position": channel.position,
        "type": str(channel.type), "bitrate": channel.bitrate,
        "voice_members": list(map(lambda member: {"name": member.name, "id": member.id}, channel.voice_members)),
        "user_limit": channel.user_limit, "is_default": channel.is_default, "created_at": str(channel.created_at)
    }, server.channels))
    role_hierarchy = list(map(lambda role: {"name": role.name, "colour": role.colour.value,
                                            "permissions": role.permissions.value}, server.role_hierarchy))
    server_json = {
        "name": server.name,
        "id": server.id,
        "roles": roles,
        "members": members,
        "channels": channels,
        "icon_url": server.icon_url,
        "owner": {"name": server.owner.name, "id": server.owner.id},
        "unavailable": server.unavailable,
        "large": server.large,
        "mfa_level": server.mfa_level,
        "verification_level": str(server.verification_level),
        "member_count": server.member_count,
        "created_at": str(server.created_at),
        "role_hierarchy": role_hierarchy
    }
    return server_json


class OhminatorWebServer:
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
        try:
            response = await websocket.recv()
            if response == "get_total_users":
                await self.get_total_users(websocket, path)
            elif response == "get_servers":
                await self.get_servers(websocket, path)
            elif response == "get_server_info":
                await self.get_server_info(websocket, path)
            elif response == "get_member_info":
                await self.get_member_info(websocket, path)
            elif response == "get_yt_list":
                await self.get_yt_list(websocket, path)
        except:
            traceback.print_exc()

    async def get_member_info(self, websocket, path):
        server_id = await websocket.recv()
        server = discord.utils.find(lambda server: server.id == server_id, self.client.servers)
        if not server:
            await websocket.send(generate_error("NoServerError", "No server exists with that ID."))
            return
        """
        member_id = await websocket.recv()
        member = discord.utils.find(lambda member: member.id == member_id, server.members)
        if not member:
            await websocket.send(generate_error("NoMemberError", "No member exists with that ID."))
            return
        """
        await websocket.send(json.dumps(generate_server_json(server)))

    async def get_server_info(self, websocket, path):
        server_id = await websocket.recv()
        server = discord.utils.find(lambda server: server.id == server_id, self.client.servers)
        if not server:
            await websocket.send(generate_error("NoServerError", "No server exists with that ID."))
            return
        await websocket.send(json.dumps({"response": "server", "data": generate_server_json(server)}))

    async def get_total_users(self, websocket, path):
        servers = sum(1 for _ in self.client.servers)
        users = sum(1 for _ in self.client.get_all_members())
        response = "Ohminator is currently serving {} server{}, {} user{}.".format(
            servers, "s" if servers != 1 else "", users, "s" if users != 1 else "")
        await websocket.send(response)

    async def get_yt_list(self, websocket, path):
        server_id = await websocket.recv()
        server = discord.utils.find(lambda server: server.id == server_id, self.client.servers)
        if not server:
            await websocket.send(generate_error("NoServerError", "No server exists with that ID."))
            return
        ohm_server_object = utils.get_server(server)
        active_player = ohm_server_object.active_playlist_element
        if not active_player:
            currently_playing = {"title": "Nothing is currently playing", "duration": 0,
                                 "webpage_url": "", "thumbnail": ""}
        else:
            currently_playing = {
                "title": active_player.title, "duration": active_player.duration,
                "webpage_url": active_player.webpage_url, "thumbnail": active_player.thumbnail
            }
        playlist_json = {
            "currently_playing": currently_playing,
            "queue": list(map(lambda element: {
                "title": element.title, "duration": element.duration,
                "webpage_url": element.webpage_url, "thumbnail": element.thumbnail
            }, ohm_server_object.playlist.yt_playlist))
        }
        await websocket.send(json.dumps({"response": "yt_playlist", "data": playlist_json}))

    async def get_servers(self, websocket, path):
        servers = list(map(lambda server: OrderedDict([("name", server.name), ("id", server.id), ("population", len(server.discord_server.members))]), utils.server_list))
        await websocket.send(json.dumps(servers))

    def setup_server(self, loop=None):
        start_server = websockets.serve(self.message_handler, '127.0.0.1', 5678)
        if not loop:
            loop = asyncio.get_event_loop()
        print("Starting web socket!")
        loop.run_until_complete(start_server)
