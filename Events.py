import discord
from random import randint
from os.path import isdir
from os import mkdir, listdir
import traceback
import time
import asyncio

from Member import Member
from Server import Server
from PlayButtons import PlayButtons
import random
import cleverbot
import youtube_dl

from utils import get_server, get_bot_channel
import utils

from audio import *
from intro import *
from admin import *

commands = dict()
cb = cleverbot.Cleverbot()
running = False
client = None


class Events:
    def __init__(self, bot: discord.Client):
        global client
        client = bot
        bot.async_event(on_ready)
        bot.async_event(on_message)
        bot.async_event(on_voice_state_update)
        bot.async_event(on_server_join)
        bot.async_event(on_member_join)
        bot.async_event(on_reaction_add)

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
            new_server = Server(server, client)
            utils.server_list.append(new_server)

            new_server.bot_channel = discord.utils.find(lambda c: c.name == 'bot-spam', server.channels)
            # If channel does not exist - create it
            if new_server.bot_channel is None:
                new_server.bot_channel = await client.create_channel(server, 'bot-spam')
        print('Done!')
        running = True
    #else:
        #try:
            #for server in server_list:
                #await client.send_message(server.bot_channel, 'Ohminator lost connection to Discord. Back now!')
        #except:
            #traceback.print_exc()


async def on_message(message):
    cmd = message.content

    bot_channel = get_bot_channel(message.server)
    if bot_channel is None:
        bot_channel = message.channel

    if len(cmd.split()) < 1:
        return

    # Normal commands can be awaited and is therefore in their own functions
    for key in commands:
        if cmd.lower().split()[0] == key:
            await commands[key](message, bot_channel, client)
            return

    # Commands that require high performance can not be awaited and are therefore implemented here
    if cmd.lower().startswith('!yt'):
        link = cmd[4:]
        await client.delete_message(message)

        # The user must be in a channel to play their link.
        if message.author.voice_channel is None or message.author.voice.is_afk:
            await client.send_message(bot_channel,
                                      '{}: Please join a voice channel to play your link!'.format(
                                          message.author.name))
            return

        # Check if the voice client is okay to use. If not, it is changed.
        # The voice client is retrieved later when the playlist starts a new song.
        voice_client = client.voice_client_in(message.author.server)
        try:
            if voice_client is None:
                voice_client = await client.join_voice_channel(message.author.voice_channel)
            elif voice_client.channel is None:
                await voice_client.disconnect()
                voice_client = await client.join_voice_channel(message.author.voice_channel)
        except:
            await client.send_message(bot_channel,
                                      '{}: Could not connect to voice channel!'.format(message.author.name))
            traceback.print_exc()
            return

        # Three cases: Case one: An intro is currently playing, so we either append or pause the active player.
        # Case two: Something is already playing, so we queue the requested songs
        # Case three: Nothing is playing, so we just start playing the song
        server = get_server(message.server)
        await server.playlist.add_to_playlist_lock.acquire()
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
                    await client.send_message(bot_channel,
                                              '{}: \nNow playing: {}\nIt is {} seconds long'.format(
                                                  message.author.name,
                                                  server.active_player.title,
                                                  server.active_player.duration))
                    server.active_player.start()
                    server.active_player.pause()

            elif server.active_player is not None and (
                        not server.active_player.is_done() or server.active_player.is_playing()) \
                    or len(server.playlist.yt_playlist) > 0:
                player = await server.playlist.add_to_playlist(link, True, message.author.name)
            else:
                # Move to the user's voice channel
                try:
                    if voice_client.channel != message.author.voice_channel:
                        await voice_client.move_to(message.author.voice_channel)
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
                await client.send_message(bot_channel,
                                          '{}: \nNow playing: {}\nIt is {} seconds long'.format(
                                              message.author.name,
                                              server.active_player.title,
                                              server.active_player.duration))
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
            server.playlist.add_to_playlist_lock.release()


async def ping(message, bot_channel, client):
    await client.delete_message(message)
    await client.send_message(bot_channel, 'Pong!')


commands["!ping"] = ping


async def help(message, bot_channel, client):
    await client.delete_message(message)
    if message.content.lower().startswith('!help sound'):
        help_resource = 'help_sound.txt'
    else:
        help_resource = 'help.txt'
    with open('resources/{}'.format(help_resource)) as f:
        help_message = f.read()
    await client.send_message(bot_channel, "{}:\n{}".format(message.author.name, help_message))


commands["!help"] = help


async def roll(message, bot_channel, client):
    try:
        options = message.content.split()
        rand = randint(int(options[1]), int(options[2]))
        await client.send_message(bot_channel, '{}: You rolled {}!'.format(message.author.name, rand))
    except:
        await client.send_message(bot_channel,
                                  '{}: Could not roll with those parameters!'.format(message.author.name))


commands["!roll"] = roll

# Audio commands
commands["!tts"] = text_to_speech
commands["!say"] = text_to_speech
commands["!volume"] = volume
commands["!sv"] = volume
commands["!stop"] = stop
commands["!pause"] = pause
commands["!resume"] = resume
commands["!delete"] = delete
commands["!skip"] = skip
commands["!q"] = queue_page
commands["!queue"] = q
commands["!next"] = next
commands["!vote"] = vote
commands["!queuepage"] = queue_page

# Intro commands
commands["!introstop"] = introstop
commands["!intro"] = intro
commands["!myintros"] = myintros
commands["!deleteintro"] = deleteintro
commands["!upload"] = upload

async def slot(message, bot_channel, client):
    await client.delete_message(message)
    if message.channel != bot_channel:
        await client.send_message(message.channel, '{}: Check bot-spam for the result!'.format(message.author.name))
    #symbols = {
    #    '0': ':no_entry_sign:',
    #    '20': ':green_apple:',
    #    '30': ':apple:',
    #    '40': ':cherries:',
    #    '80': ':sun_with_face:',
    #    '100': ':bulb:',
    #    '120': ':heart:',
    #    '300': ':alien:',
    #    '600': ':moneybag:'
    #}
    symbols = {
        ':moneybag:': 600,
        ':four_leaf_clover:': 300,
        ':heart:': 120,
        ':bulb:': 100,
        ':sun_with_face:': 80,
        ':alien:': 40,
        ':apple:': 30,
        ':cherries:': 0,
    }
    symbols_list = list(symbols.keys())
    rand = randint(8, 63)
    num = len(symbols_list)
    first_column = [symbols_list[(rand-1)%num], symbols_list[rand%num], symbols_list[(rand+1)%num]]
    rand = randint(8, 63)
    second_column = [symbols_list[(rand-1)%num], symbols_list[rand%num], symbols_list[(rand+1)%num]]
    rand = randint(8, 63)
    third_column = [symbols_list[(rand-1)%num], symbols_list[rand%num], symbols_list[(rand+1)%num]]

    #first_column = random.choice([k for k in symbols for dummy in range(symbols[k])])
    #second_column = random.choice([k for k in symbols for dummy in range(symbols[k])])
    #third_column = random.choice([k for k in symbols for dummy in range(symbols[k])])

    if first_column[1] is second_column[1] is third_column[1]:
        result = "Congratulations, you won!"
    else:
        result = "Sorry, but you lost..."
    slot_string = "  {}{}{}\n>{}{}{}<\n  {}{}{}\n\n{}".format(first_column[0], second_column[0], third_column[0],
                                                            first_column[1], second_column[1], third_column[1],
                                                            first_column[2], second_column[2], third_column[2], result)
    await client.send_message(bot_channel, '{}: Good luck!\n\n{}'.format(message.author.name, slot_string))

commands["!slot"] = slot

async def joined(message, bot_channel, client):
    await client.delete_message(message)
    await client.send_message(bot_channel, '{}: You joined the Ohm server {}!'.format(message.author.name,
                                                                                      message.author.joined_at))

commands["!joined"] = joined

async def ask(message, bot_channel, client):
    question = message.content[5:]
    try:
        await client.send_message(message.channel, cb.ask(question))
    except IndexError as e:
        traceback.print_exc()
        await client.send_message(message.channel,
                                  '{}: Sorry, it seems cleverbot is not functioning at the moment!'
                                  ''.format(message.author.mention))
    except Exception as e:
        traceback.print_exc()
        await client.send_message(message.channel,
                                  '{}: That is not a question I will answer!'.format(message.author.mention))


commands["!ask"] = ask

async def suggest(message, bot_channel, client):
    suggestion = message.content[9:]
    if len(suggestion) < 3:
        await client.send_message(bot_channel,
                                  "{}: Please suggest something proper.".format(message.author.mention))
        return
    server = get_server(message.server)
    member = server.get_member(message.author.id)
    suggestion_loc = 'suggestions.pickle'.format(server.server_loc, member.member_loc)
    with open(suggestion_loc, 'a') as f:
        f.write("Suggestion from {}:\n{}\n".format(message.author, suggestion))
    await client.send_message(bot_channel,
                              '{}: Your suggestion has been noted. Thank you!'.format(message.author.mention))


commands["!suggest"] = suggest


async def join(message, bot_channel, client):
    await client.delete_message(message)
    server = get_server(message.server)
    if message.author not in server.split_list:
        server.split_list.append(message.author)
        await client.send_message(bot_channel,
                                  '{}: You have joined the queue!\n'
                                  'Current queue: {}'.format(message.author.mention, server.print_queue()))


commands["!team join"] = join


async def leave(message, bot_channel, client):
    await client.delete_message(message)
    server = get_server(message.server)
    server.split_list.remove(message.author)
    await client.send_message(bot_channel,
                              '{}: You have left the queue!\n'
                              'Current queue: {}'.format(message.author.mention, server.print_queue()))


commands["!team leave"] = leave


async def split(message, bot_channel, client):
    await client.delete_message(message)
    try:
        num_teams = int(message.content.split()[1])
    except:
        await client.send_message(bot_channel,
                                  '{}: Invalid parameter for !split. Use number of teams!'.format(message.author.name))
        return

    channel_list = list()
    for team_number in range(num_teams):
        channel = discord.utils.get(message.author.server.channels, name='Team {}'.format(team_number + 1))
        if channel is None:
            channel_list.append(
                await client.create_channel(message.author.server, 'Team {}'.format(team_number + 1),
                                            type=discord.ChannelType.voice))
        else:
            channel_list.append(channel)

    server = get_server(message.server)
    division = len(server.split_list) / float(num_teams)
    random.shuffle(server.split_list)
    teams = [server.split_list[int(round(division * i)): int(round(division * (i + 1)))] for i in range(num_teams)]

    index = 0
    for team in teams:
        for member in team:
            await client.move_member(member, channel_list[index])
        index += 1


commands["!split"] = split


async def removeteams(message, bot_channel, client):
    await client.delete_message(message)
    team_number = 1
    while True:
        channel = discord.utils.get(message.author.server.channels, name='Team {}'.format(team_number))
        if channel is None:
            break
        else:
            await client.delete_channel(channel)
        team_number += 1


commands["!removeteams"] = removeteams


async def get_bot_invite(message, bot_channel, client):
    await client.delete_message(message)
    permissions = discord.Permissions.all()
    await client.send_message(message.channel,
                              '{}: {}'.format(message.author.name,
                                              discord.utils.oauth_url('176432800331857920', permissions=permissions)))


commands["!getbotinvite"] = get_bot_invite


async def settings(message, bot_channel, client):
    await client.delete_message(message)
    tokens = message.content.split()
    if len(tokens) < 2:
        await client.send_message(message.channel,
                                  '{}: Usage !settings [client name or id] [([permission to change]'
                                  ' [value to change to])]'.format(message.author.name))
        return
    server = get_server(message.server)
    if tokens[1] == message.server.id:
        settings_source = server
    else:
        settings_source = server.get_channel(tokens[1])
    if len(tokens) < 3:
        # No other arguments -> list all settings for given channel
        settings_str = "Settings for {} {}:".format("server" if settings_source == server else "channel", settings_source.name)
        for key, val in settings_source.list_settings().items():
            settings_str += "\n{}: {}".format(key, val)
        await client.send_message(message.channel,
                                  '{}: {}'.format(message.author.name, settings_str))
    elif len(tokens) < 4:
        await client.send_message(message.channel,
                                  '{}: Usage !settings [client/server name or id] [([permission to change]'
                                  ' [value to change to])]'.format(message.author.name))
    else:
        if tokens[2] in settings_source.list_settings().keys():
            settings_source.change_settings({tokens[2] : tokens[3]})
            await client.send_message(message.channel,
                                      '{}: The setting {} har been changed to {}.'.format(message.author.name, tokens[2], tokens[3]))
        else:
            await client.send_message(message.channel,
                                      '{}: The setting {} does not exist.'.format(message.author.name, tokens[2]))

commands["!settings"] = settings


async def playbuttons(message, bot_channel, client):
    await client.delete_message(message)
    server = get_server(message.server)
    lock = asyncio.locks.Lock()
    await lock.acquire()
    await client.send_message(message.channel, 'Here are buttons for controlling the playlist.\n'
                                               'Use reactions to trigger them!')
    play = await client.send_message(message.channel, 'Play :arrow_forward:')
    pause = await client.send_message(message.channel, 'Pause :pause_button:')
    stop = await client.send_message(message.channel, 'Stop :stop_button:')
    next = await client.send_message(message.channel, 'Next song :track_next:')
    volume_up = await client.send_message(message.channel, 'Volume up :heavy_plus_sign:')
    volume_down = await client.send_message(message.channel, 'Volume down :heavy_minus_sign:')
    queue = await client.send_message(message.channel, 'Current queue :notes:')
    await client.send_message(message.channel, '----------------------------------------')
    server.playbuttons = PlayButtons(play, pause, stop, next, volume_up, volume_down, queue)
    lock.release()

commands["!playbuttons"] = playbuttons

async def on_reaction_add(reaction, user):
    server = get_server(reaction.message.server)
    if server.playbuttons is not None:
        await server.playbuttons.handle_message(reaction.message, server, client)

    if server.queue_pages is not None:
        if reaction.message.id == server.queue_pages.message.id:
            await server.queue_pages.print_next_page(client)


async def on_voice_state_update(before, after):
    if after.voice_channel is None or after.voice.is_afk or (before.voice_channel is after.voice_channel):
        return
    server = get_server(after.server)
    if server is None:
        return
    member = server.get_member(after.id)
    if not member.has_intro():
        return

    voice_client = client.voice_client_in(after.server)
    try:
        if voice_client is None:
            voice_client = await client.join_voice_channel(after.voice_channel)
        elif voice_client.channel is None:
            await voice_client.disconnect()
            voice_client = await client.join_voice_channel(after.voice_channel)
        elif voice_client.channel != after.voice_channel:
            await voice_client.move_to(after.voice_channel)
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
        intro_list = listdir('servers/{}/members/{}/intros'.format(server.server_loc, member.member_loc))
        server.intro_player = voice_client.create_ffmpeg_player(
            'servers/{}/members/{}/intros/{}'.format(server.server_loc, member.member_loc,
                                                     random.choice(intro_list)),
            after=server.intro_manager.after_intro)
        server.intro_player.volume = 0.25
        server.intro_player.start()
        await server.intro_manager.intro_counter_lock.acquire()
        server.intro_manager.intro_counter += 1
        server.intro_manager.intro_counter_lock.release()
    except Exception as e:
        print(e)


async def on_server_join(server):
    server_loc = '{}_{}'.format(server.name, server.id)
    if not isdir('servers/{}'.format(server_loc)):
        mkdir('servers/{}'.format(server_loc))
    new_server = Server(server, client)
    utils.server_list.append(new_server)

    new_server.bot_channel = discord.utils.find(lambda c: c.name == 'bot-spam', server.channels)
    # If channel does not exist - create it
    if new_server.bot_channel is None:
        new_server.bot_channel = await client.create_channel(server, 'bot-spam')


async def on_member_join(member):
    server = get_server(member.server)
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
