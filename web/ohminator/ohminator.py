import os
import time

import discord
import ohminator.utils as utils
from ohminator.member import Member
from ohminator.server import Server

from functools import wraps
from ohminator_web.models import Guild, User, Plugin

from ohminator.plugins import *

running = False


class Ohminator(discord.Client):

    def __init__(self, **options):
        super().__init__(**options)

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print(discord.version_info)
        print(discord.__version__)
        print('------')
        global running
        if not running:
            print('[{}]: Setting up data structures...'.format(time.strftime('%a, %H:%M:%S')))
            utils.create_if_not_exists('servers')
            for guild in self.guilds:
                new_server = Server(guild, self, None)
                utils.server_list.append(new_server)
                new_server.bot_channel = discord.utils.find(lambda c: c.name == 'bot-spam', guild.channels)
                # If channel does not exist - create it
                if new_server.bot_channel is None:
                    new_server.bot_channel = await guild.create_text_channel('bot-spam')
                # Change the topic of the channel if not already set
                with open('resources/bot_channel_topic.txt') as f:
                    topic = f.read()
                if new_server.bot_channel.topic != topic:
                    await new_server.bot_channel.edit(topic=topic)
            print('Done!')
            running = True

    async def on_message(self, message):
        if message.content.strip() and message.guild:
            guild = Guild.objects.get(pk=message.guild.id)
            # Normal commands can be awaited and are therefore in their own functions
            for key in commands:
                if message.content.lower().split()[0] == guild.prefix + key:
                    await commands[key](message, self, guild, None)
                    return


def run_ohminator():
    client = Ohminator()

    # Reads token
    with open("web/token.txt", 'r') as f:
        token = f.read().strip()

    # Starts the execution of the bot
    client.run(token)


class CommandAlreadyExistsError(BaseException):
    def __init__(self, command):
        super(CommandAlreadyExistsError, self).__init__("Command '{}' already exists!".format(command))


commands = utils.commands


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
        async def wrapped(message, client, guild, plugin):
            return await func(message, client, guild, plugin)
