import asyncio
from functools import wraps
from os.path import exists
from os import mkdir

import discord

server_list = list()
commands = dict()
playlists = dict()


# Registers new commands
class RegisterCommand:

    def __init__(self, *args, plugin=None):
        self.args = args
        self.plugin = plugin

    def __call__(self, func, *args, **kwargs):
        for command in self.args:
            if command in commands:
                raise CommandAlreadyExistsError(command)
            commands[command] = func

        @wraps(func)
        async def wrapped(message, client, plugin):
            return await func(message, client, plugin)

        return wrapped


def create_if_not_exists(path):
    if not exists(path):
        mkdir(path)


def create_now_playing_embed(now_playing):
    embed = discord.Embed()
    embed.title = "Now playing:"
    embed.colour = discord.Colour.dark_green()
    embed.description = f'[{now_playing["title"]}]({now_playing["url"]})\n' \
                        f'It is {int(now_playing["duration"])} seconds long.'
    if now_playing["thumbnail"]:
        #low_res_thumbnail = now_playing["thumbnail"]
        #url_splitted = low_res_thumbnail.split('/')
        #url_splitted[-1] = 'mqdefault.jpg'
        #high_res_thumbnail = '/'.join(url_splitted)
        embed.set_thumbnail(url=now_playing["thumbnail"])
    return embed


def update_active_player(audio_source, guilds_ref, user):
    active_player = {
        "title": audio_source.title, "volume": audio_source.volume,
        "thumbnail": audio_source.data["thumbnail"], "extractor": audio_source.data["extractor"],
        "duration": audio_source.data["duration"], "url": audio_source.data["webpage_url"],
        "type": "youtube-dl", "status": "playing", "user": user
    }
    guilds_ref.update({"active_player": active_player})
    return active_player


class NoChannelFoundError(BaseException):
    pass


class NoMemberFoundError(BaseException):
    pass


class CommandAlreadyExistsError(BaseException):
    def __init__(self, command):
        super(CommandAlreadyExistsError, self).__init__(f"Command '{command}' already exists!")
