import os
import discord

from functools import wraps
from ohminator_web.models import Guild, User, Plugin


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

    async def on_message(self, message):
        if message.content.strip() and message.guild:
            guild = Guild.objects.get(pk=message.guild.id)
            # Normal commands can be awaited and is therefore in their own functions
            for key in commands:
                if message.content.lower().split()[0] == guild.prefix + key:
                    await commands[key](message, self, None)
                    return


def run_ohminator():
    client = Ohminator()

    # Reads token
    with open("token.txt", 'r') as f:
        token = f.read().strip()

    # Starts the execution of the bot
    client.run(token)


class CommandAlreadyExistsError(BaseException):
    def __init__(self, command):
        super(CommandAlreadyExistsError, self).__init__("Command '{}' already exists!".format(command))


commands = {}


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


@RegisterCommand('info', 'help', 'commands', plugin=None)
async def info(message, client, plugin):
    await message.channel.send('Halla balla!')
