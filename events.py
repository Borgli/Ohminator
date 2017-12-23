import asyncio
import random
import time
import traceback
from os import mkdir, listdir
from os.path import isdir

import discord
import youtube_dl

import utils
from member import Member
from server import Server
from admin import notify_of_joining_person, notify_of_leaving_person, assign_default_role

# Plugins
from plugins import *

# Websocket server
import web.web_server as web

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
        web_server = web.OhminatorWebServer(client)
        web_server.setup_server()


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

    parameters = cmd.split()
    # Commands that require high performance can not be awaited and are therefore implemented here
    if parameters[0].lower() == server.prefix + 'yt' or parameters[0].lower() == server.prefix + 'play' \
            or parameters[0].lower() == server.prefix + 'p':
        await client.delete_message(message)

        if len(parameters) < 2:
            await client.send_message(bot_channel,
                                      '{}: Usage: !yt or !play or !p [link or search term]!'.format(
                                          message.author.name))
            return

        link = " ".join(message.content.split()[1:])

        # The user must be in a channel to play their link.
        if message.author.voice_channel is None or message.author.voice.is_afk:
            await client.send_message(bot_channel,
                                      '{}: Please join a voice channel to play your link!'.format(
                                          message.author.name))
            return

        if server.playlist.summoned_channel:
            # Restricts users to only be able to add songs to playlist if they are in the channel the bot is locked to.
            if message.author.voice.voice_channel == server.playlist.summoned_channel:
                voice_channel = server.playlist.summoned_channel
            else:
                await client.send_message(bot_channel,
                                          '{}: The bot is locked to channel {}. '
                                          'Please join that channel to make Ohminator play audio.'.format(
                                              message.author.name, server.playlist.summoned_channel.name))
                return
        else:
            voice_channel = message.author.voice_channel
        # Check if the voice client is okay to use. If not, it is changed.
        # The voice client is retrieved later when the playlist starts a new song.
        voice_client = client.voice_client_in(message.author.server)
        try:
            if voice_client is None:
                voice_client = await client.join_voice_channel(voice_channel)
            elif voice_client.channel is None:
                await voice_client.disconnect()
                voice_client = await client.join_voice_channel(voice_channel)
        except:
            await client.send_message(bot_channel,
                                      '{}: Could not connect to voice channel!'.format(message.author.name))
            traceback.print_exc()
            return

        # Three cases: Case one: An intro is currently playing, so we either append or pause the active player.
        # Case two: Something is already playing, so we queue the requested songs
        # Case three: Nothing is playing, so we just start playing the song
        await server.playlist.playlist_lock.acquire()
        if server.active_tts:
            server.active_tts.stop()
            server.tts_queue.clear()
        try:
            # Must check if intro is already playing
            if server.intro_player is not None and server.intro_player.is_playing():
                # Check if there's something in the playlist
                if len(server.playlist.yt_playlist) > 0:
                    player = await server.playlist.add_to_playlist(link, True, message.author.name)
                else:
                    player = await server.playlist.add_to_playlist(link, False, message.author.name)
                    server.active_player = await player.get_new_player()
                    server.active_playlist_element = player
                    server.playlist.now_playing = server.active_player.title
                    await client.send_message(bot_channel, '{}:'.format(message.author.name),
                                              embed=utils.create_now_playing_embed(server.active_playlist_element))
                    server.active_player.start()
                    server.active_player.pause()

            elif server.active_player is not None and (
                        not server.active_player.is_done() or server.active_player.is_playing()) \
                    or len(server.playlist.yt_playlist) > 0:
                player = await server.playlist.add_to_playlist(link, True, message.author.name)
            else:
                # Move to the user's voice channel
                try:
                    if voice_client.channel != voice_channel:
                        await voice_client.move_to(voice_channel)
                except:
                    await client.send_message(bot_channel,
                                              '{}: Could not connect to voice channel!'.format(message.author.name))
                    print("Couldn't move from channel {} to channel {}!".format(voice_client.channel.name,
                                                                         message.author.voice_channel.name))
                    traceback.print_exc()
                    return

                player = await server.playlist.add_to_playlist(link, False, message.author.name)
                server.active_player = await player.get_new_player()
                server.active_playlist_element = player
                server.playlist.now_playing = server.active_player.title
                await client.send_message(bot_channel, '{}:'.format(message.author.name),
                                          embed=utils.create_now_playing_embed(server.active_playlist_element))
                server.active_player.start()
        except youtube_dl.utils.UnsupportedError:
            await client.send_message(bot_channel,
                                      '{}: Unsupported URL: That URL is not supported! :slight_frown:'.format(
                                          message.author.name))
        except youtube_dl.utils.DownloadError:
            await client.send_message(bot_channel,
                                      '{}: Download Error: Your link could not be downloaded! :slight_frown:'.format(
                                          message.author.name))
        except youtube_dl.utils.MaxDownloadsReached:
            await client.send_message(bot_channel,
                                      '{}: Max downloads reached: Can not download more videos from YT at the moment. '
                                      'Please wait a moment before trying again. :slight_frown:'.format(
                                          message.author.name))
        except youtube_dl.utils.UnavailableVideoError:
            await client.send_message(bot_channel,
                                      '{}: Unavailable Video: This video is unavailable! :slight_frown:'.format(
                                          message.author.name))
        except:
            await client.send_message(bot_channel,
                                      '{}: Your link could not be played!'.format(message.author.name))
            traceback.print_exc()
        finally:
            server.playlist.playlist_lock.release()


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

    # Handles playing intros when the bot is summoned
    if server.playlist.summoned_channel:
        if after.voice_channel == server.playlist.summoned_channel:
            voice_channel = server.playlist.summoned_channel
        else:
            return
    else:
        voice_channel = after.voice_channel

    voice_client = client.voice_client_in(after.server)
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
        server.intro_manager.intro_counter += 1
    except Exception as e:
        print(e)
    finally:
        server.intro_manager.intro_counter_lock.release()


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
