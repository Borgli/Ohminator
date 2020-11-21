import os
import sys
import time

import discord
import utils

from functools import wraps

import firebase_admin
from firebase_admin import credentials, db

from utils import RegisterCommand

import plugins.audio_player

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
            # sync guilds
            guilds_ref = db.reference('guilds')
            guilds_snapshot = guilds_ref.order_by_key().get()
            for guild in self.guilds:
                if guilds_snapshot is None or str(guild.id) not in guilds_snapshot:
                    bot_channel = discord.utils.find(lambda c: c.name == 'bot-spam', guild.channels)
                    # If channel does not exist - create it
                    if bot_channel is None:
                        bot_channel = await guild.create_text_channel('bot-spam')
                        # Change the topic of the channel if not already set
                        with open('resources/bot_channel_topic.txt') as f:
                            topic = f.read()
                        if bot_channel.topic != topic:
                            await bot_channel.edit(topic=topic)
                    guilds_ref.update({
                        guild.id: {"name": guild.name, "bot_channel": bot_channel.id, "prefix": "!",
                                   "commands": {key: True for key in commands.keys()}, "playlist": [],
                                   "summoned_channel": None}
                    })
            print('Done!')
            running = True

    async def on_message(self, message):
        if message.content.strip() and message.guild:
            guild_ref = db.reference(f"guilds/{message.guild.id}/").get()
            # Normal commands can be awaited and are therefore in their own functions
            for key in guild_ref["commands"]:
                if guild_ref["commands"][key] and message.content.lower().split()[0] == guild_ref["prefix"] + key:
                    await commands[key](message, message.guild.get_channel(guild_ref["bot_channel"]), self, guild_ref)
                    return


def run_ohminator():
    # Initializes firebase

    cred = credentials.Certificate("../firebase_key.json")
    default_app = firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://ohminator-1337.firebaseio.com/'
    })

    # Initializes bot
    client = Ohminator()

    # Reads token
    with open("../token.txt", 'r') as f:
        token = f.read().strip()

    # Starts the execution of the bot
    try:
        client.run(token)
    except discord.errors.LoginFailure:
        print("Invalid token.")
    finally:
        client.close()


class CommandAlreadyExistsError(BaseException):
    def __init__(self, command):
        super(CommandAlreadyExistsError, self).__init__("Command '{}' already exists!".format(command))


@RegisterCommand("ping")
async def ping(message, bot_channel, client):
    await client.delete_message(message)
    await client.send_message(bot_channel, 'Pong!')


@RegisterCommand("joined")
async def joined(message, bot_channel, client):
    await client.delete_message(message)
    await client.send_message(bot_channel, '{}: You joined the Ohm server {}!'.format(message.author.name,
                                                                                      message.author.joined_at))


@RegisterCommand("roll")
async def roll(message, bot_channel, client, guild):
    await message.delete()
    try:
        options = message.content.split()
        from random import randint
        rand = randint(int(options[1]), int(options[2]))
        await bot_channel.send('{}: You rolled {}!'.format(message.author.name, rand))
    except:
        await bot_channel.send('{}: USAGE: !roll [lowest] [highest]'.format(message.author.name))



commands = utils.commands

if __name__ == '__main__':
    run_ohminator()


