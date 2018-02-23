import asyncio
import random
import time
import traceback
import string
from os import mkdir, listdir
from os.path import isdir
from collections import Counter

import discord
import youtube_dl

import utils
from member import Member
from server import Server
from admin import notify_of_joining_person, notify_of_leaving_person, assign_default_role

# Plugins
from plugins import *

commands = utils.commands
running = False
client = None
db = None


class Events:
    def __init__(self, bot: discord.Client, database):
        global client
        client = bot
        global db
        db = database
        bot.async_event(on_ready)
        bot.async_event(on_message)
        bot.async_event(on_voice_state_update)
        bot.async_event(on_server_join)
        bot.async_event(on_member_join)
        bot.async_event(on_reaction_add)
        client.loop.create_task(set_global_text())


async def set_global_text():
    await client.wait_until_ready()
    await asyncio.sleep(10, loop=client.loop)
    while not client.is_closed:
        await client.change_presence(game=discord.Game(
            name="ohminator.com | !help", type=1))
        await asyncio.sleep(300, loop=client.loop)


async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print(discord.version_info)
    print(discord.__version__)
    print('------')
    global running
    if not running:
        print('[{}]: Setting up data structures...'.format(time.strftime('%a, %H:%M:%S')))
        if not isdir('servers'):
            mkdir('servers')
        for server in client.servers:
            server_loc = '{}_{}'.format(server.name, server.id)
            if not isdir('servers/{}'.format(server_loc)):
                mkdir('servers/{}'.format(server_loc))
            new_server = Server(server, client, db)
            utils.server_list.append(new_server)

            new_server.bot_channel = discord.utils.find(lambda c: c.name == 'bot-spam', server.channels)
            # If channel does not exist - create it
            if new_server.bot_channel is None:
                new_server.bot_channel = await client.create_channel(server, 'bot-spam')
            # Change the topic of the channel if not already set
            with open('resources/bot_channel_topic.txt') as f:
                topic = f.read()
            if new_server.bot_channel.topic != topic:
                await client.edit_channel(new_server.bot_channel, topic=topic)
        print('Done!')
        running = True


async def on_message(message):
    cmd = message.content

    bot_channel = utils.get_bot_channel(message.server)
    if bot_channel is None:
        bot_channel = message.channel

    if len(cmd.split()) < 1:
        return

    server = utils.get_server(message.server)
    # Normal commands can be awaited and is therefore in their own functions
    for key in commands:
        if cmd.lower().split()[0] == server.prefix + key:
            await commands[key](message, bot_channel, client)
            return
    await suggest_correct_command(message)


async def suggest_correct_command(message):
    cmd = message.content.lower().split()[0][1:]
    for command in commands.keys():
        # Check for anagrams
        if Counter(cmd) == Counter(command):
            await client.send_message(message.channel,
                                      "{}: Did you mean '{}'?".format(message.author.name, command))
            return
        # Check for anagrams with missing letters
        for letter in string.ascii_lowercase:
            if Counter(cmd+letter) == Counter(command):
                await client.send_message(message.channel,
                                          "{}: Did you mean '{}'?".format(message.author.name, command))
                return
        # Check for anagrams with added letters
        for index in range(len(cmd)):
            if Counter(cmd[:index] + cmd[(index+1):]) == Counter(command):
                await client.send_message(message.channel,
                                          "{}: Did you mean '{}'?".format(message.author.name, command))
                return


async def on_reaction_add(reaction, user):
    server = utils.get_server(reaction.message.server)
    if server.playbuttons is not None:
        await server.playbuttons.handle_message(reaction.message, server, client)

    if server.queue_pages is not None:
        if reaction.message.id == server.queue_pages.message.id:
            await server.queue_pages.print_next_page(client)


async def on_voice_state_update(before, after):
    if after.id == client.user.id:
        return
    if after.voice_channel is None or after.voice.is_afk or (before.voice_channel is after.voice_channel):
        return
    server = utils.get_server(after.server)
    if server is None:
        return

    member = server.get_member(after.id)
    default_intros = listdir('servers/{}/default_intros'.format(server.server_loc))
    if member.has_intro():
        intro_source = 'servers/{}/members/{}/intros'.format(server.server_loc, member.member_loc)
    elif len(default_intros) > 0:
        intro_source = 'servers/{}/default_intros'.format(server.server_loc)
    else:
        return

    await server.intro_manager.intro_lock.acquire()
    try:
        # Handles playing intros when the bot is summoned
        if server.playlist.summoned_channel:
            if after.voice_channel == server.playlist.summoned_channel:
                voice_channel = server.playlist.summoned_channel
            else:
                return
        else:
            voice_channel = after.voice_channel

        # New approach to connecting to voice client. Before it would be problematic
        # as it would not refresh the server region when it changed and would therefore
        # stop playing. This solution introduces a race condition which needs a lock.
        voice_client = await utils.connect_to_voice(client, after.server, voice_channel)

        # voice_client = client.voice_client_in(after.server)
        '''
        try:
            if voice_client is None:
                voice_client = await client.join_voice_channel(voice_channel)
            elif voice_client.channel is None:
                await voice_client.disconnect()
                voice_client = await client.join_voice_channel(voice_channel)
            elif voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)
        except Exception as e:
            print(e)
            return
        '''

        if server.active_tts:
            server.active_tts.stop()
            server.tts_queue.clear()

        if server.active_player is not None and server.active_player.is_playing():
            server.active_player.pause()

        if server.intro_player is not None and server.intro_player.is_playing():
            server.intro_player.stop()

        try:
            intro_list = listdir(intro_source)
            server.intro_player = voice_client.create_ffmpeg_player(
                '{}/{}'.format(intro_source, random.choice(intro_list)),
                after=server.intro_manager.after_intro)
            server.intro_player.volume = 0.25
            server.intro_player.start()
            await server.intro_manager.intro_counter_lock.acquire()
            try:
                server.intro_manager.intro_counter += 1
            finally:
                server.intro_manager.intro_counter_lock.release()
        except Exception as e:
            print(e)
    finally:
        server.intro_manager.intro_lock.release()


async def on_server_join(server):
    server_loc = '{}_{}'.format(server.name, server.id)
    if not isdir('servers/{}'.format(server_loc)):
        mkdir('servers/{}'.format(server_loc))
    new_server = Server(server, client, db)
    utils.server_list.append(new_server)

    new_server.bot_channel = discord.utils.find(lambda c: c.name == 'bot-spam', server.channels)
    # If channel does not exist - create it
    if new_server.bot_channel is None:
        new_server.bot_channel = await client.create_channel(server, 'bot-spam')
    # Change the topic of the channel if not already set
    with open('resources/bot_channel_topic.txt') as f:
        topic = f.read()
    if new_server.bot_channel.topic != topic:
        await client.edit_channel(new_server.bot_channel, topic=topic)


async def on_server_remove(server):
    server = utils.get_server(server)
    for task in server.playlist.task_list:
        task.cancel()
    utils.server_list.remove(server)


async def on_member_join(member):
    server = utils.get_server(member.server)
    member_loc = '{}-{}'.format(member.name, member.id)
    if not isdir('servers/{}/members/{}'.format(server.server_loc, member_loc)):
        mkdir('servers/{}/members/{}'.format(server.server_loc, member_loc))
    server.member_list.append(Member(client, server, member))
    if member.server.id == "159295044530995200":
        await assign_default_role(client, member, "Faggot")
    await notify_of_joining_person(client, member)


async def on_member_remove(member):
    await notify_of_leaving_person(client, member)


async def on_resumed():
    for server in utils.server_list:
        await client.send_message(server.bot_channel, 'Ohminator lost connection to Discord. Back now!')
