import asyncio
from functools import wraps
from os.path import exists
from os import mkdir

import discord

server_list = list()
commands = dict()


# Registers new commands
def register_command(*args):
    def wrapper(func):
        for command in args:
            if command in commands:
                raise CommandAlreadyExistsError(command)
            commands[command] = func

        @wraps(func)
        async def wrapped(message, bot_channel, client):
            return await func(message, bot_channel, client)

        return wrapped

    return wrapper


def create_if_not_exists(path):
    if not exists(path):
        mkdir(path)


async def connect_to_voice(client, server, voice_channel):
    voice_client = client.voice_client_in(server)
    if voice_client:
        if not server.region.value in voice_client.endpoint or not voice_client.channel:
            await voice_client.disconnect()
            voice_client = await client.join_voice_channel(voice_channel)
        elif voice_client.channel != voice_channel:
            # Some times the following code works. Other times it does not...
            # await voice_client.disconnect()
            # voice_client = await client.join_voice_channel(voice_channel)
            # ... and we have to change to this.
            await voice_client.move_to(voice_channel)
    else:
        voice_client = await client.join_voice_channel(voice_channel)
    return voice_client


def get_server(discord_server):
    for server in server_list:
        if server.id == discord_server.id:
            return server


def get_bot_channel(message_server):
    if message_server is None:
        return None
    return get_server(message_server).bot_channel


def create_now_playing_embed(now_playing):
    embed = discord.Embed()
    embed.title = "Now playing:"
    embed.colour = discord.Colour.dark_green()
    embed.description = "[{}]({})\n{}".format(now_playing.title, now_playing.webpage_url,
                                              'It is {} seconds long'.format(now_playing.duration))
    if now_playing.thumbnail:
        low_res_thumbnail = now_playing.thumbnail
        url_splitted = low_res_thumbnail.split('/')
        url_splitted[-1] = 'mqdefault.jpg'
        high_res_thumbnail = '/'.join(url_splitted)
        embed.set_thumbnail(url=high_res_thumbnail)
    return embed


class NoChannelFoundError(BaseException):
    pass


class NoMemberFoundError(BaseException):
    pass


class CommandAlreadyExistsError(BaseException):
    def __init__(self, command):
        super(CommandAlreadyExistsError, self).__init__("Command '{}' already exists!".format(command))
