import asyncio
import pickle
import threading
import urllib.request
import discord
from os import mkdir, listdir
from os.path import isdir
from random import randint
from dateutil.parser import parse

import steamapi
import youtube_dl

import utils
from Member import Member
from PlayButtons import PlayButtons
from Server import Server
from admin import *
from audio import *
from intro import *
from others import *
from wow import *

commands = dict()
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

async def set_global_text():
    await client.wait_until_ready()
    await asyncio.sleep(10, loop=client.loop)
    while not client.is_closed:
        servers = sum(1 for _ in client.servers)
        users = sum(1 for _ in client.get_all_members())
        await client.change_presence(game=discord.Game(
            name="{} server{}, {} user{}".format(
                servers, "s" if servers != 1 else "", users, "s" if users != 1 else ""), type=1))
        await asyncio.sleep(300, loop=client.loop)


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
    if cmd.lower().startswith('!yt') or cmd.lower().startswith('!play') or cmd.lower().startswith('!p'):
        await client.delete_message(message)

        parameters = message.content.split()
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

        server = get_server(message.server)
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
            server.playlist.add_to_playlist_lock.release()


async def ping(message, bot_channel, client):
    await client.delete_message(message)
    await client.send_message(bot_channel, 'Pong!')


commands["!ping"] = ping


async def print_page(resource, message, bot_channel, client, prefix_user=True):
    with open('resources/{}'.format(resource)) as f:
        content = f.read()
    help_page = "{}{}".format("{}:\n".format(message.author.name) if prefix_user else "", content)
    await client.send_message(bot_channel, help_page)

async def help(message, bot_channel, client):
    await client.delete_message(message)
    async def print_help_page(help_resource, prefix_user=True):
        return await print_page(help_resource, message, bot_channel, client, prefix_user)
    if message.content.lower().startswith('!help audio'):
        await print_help_page('help_audio.txt')
    elif message.content.lower().startswith('!help intro'):
        await print_help_page('help_intro.txt')
    elif message.content.lower().startswith('!help util'):
        await print_help_page('help_utils.txt')
    elif message.content.lower().startswith('!help other'):
        await print_help_page('help_others.txt')
    elif message.content.lower().startswith('!help all'):
        await print_help_page('help_all_1.txt')
        await print_help_page('help_all_2.txt', False)
        await print_help_page('help_all_3.txt', False)
    else:
        await print_help_page('help.txt')
        await print_help_page('summary.txt', False)


commands["!help"] = help
commands["!commands"] = help
commands["!command"] = help
commands["!info"] = help

async def summary(message, bot_channel, client):
    await client.delete_message(message)
    return await print_page('summary.txt', message, bot_channel, client)

commands["!summary"] = summary

async def roll(message, bot_channel, client):
    await client.delete_message(message)
    try:
        options = message.content.split()
        rand = randint(int(options[1]), int(options[2]))
        await client.send_message(bot_channel, '{}: You rolled {}!'.format(message.author.name, rand))
    except:
        await client.send_message(bot_channel,
                                  '{}: USAGE: !roll [lowest] [highest]'.format(message.author.name))


async def set_birthday(message, bot_channel, client):
    await client.delete_message(message)
    parameters = message.content.split()
    if len(parameters) < 2:
        await client.send_message(bot_channel,
                                  '{}: Use: !setbirthday [your birthday]'.format(message.author.name))
        return
    try:
        date = parse(" ".join(parameters[1:]), dayfirst=True, fuzzy=True)
    except ValueError:
        await client.send_message(bot_channel,
                                  '{}: Invalid birth date! Please try a different format like day/month/year'.format(message.author.name))
        return
    except OverflowError:
        await client.send_message(bot_channel,
                                  '{}: The number you gave overflowed!'.format(message.author.name))
        return
    server = utils.get_server(message.server)
    member = server.get_member(message.author.id)
    member.birthday['birthday'] = date.date()
    birthday_pickle = 'servers/{}/members/{}/birthday.pickle'.format(server.server_loc, member.member_loc)
    # Save birthday to pickle
    with open(birthday_pickle, 'w+b') as f:
        pickle.dump(member.birthday, f)
    await client.send_message(bot_channel,
                              '{}: Your birthday was set successfully.'
                              '\nIt was saved as {}.'
                              '\nPlease verify that this is correct.'.format(message.author.name, date.date()))


async def my_birthday(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    member = server.get_member(message.author.id)
    if 'birthday' in member.birthday:
        await client.send_message(bot_channel,
                                  '{}: Your birthday is {}'.format(message.author.name, member.birthday['birthday'].ctime()))
    else:
        await client.send_message(bot_channel,
                                  "{}: You don't have a birthday saved to Ohminator!"
                                  "\nYou can add one by using the !setbirthday command.".format(message.author.name))

async def clear_birthday(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    member = server.get_member(message.author.id)
    member.birthday = dict()
    # Save birthday to pickle
    birthday_pickle = 'servers/{}/members/{}/birthday.pickle'.format(server.server_loc,
                                                                     member.member_loc)
    with open(birthday_pickle, 'w+b') as f:
        pickle.dump(member.birthday, f)
    await client.send_message(bot_channel, '{}: Your birthday has been cleared.'.format(message.author.name))

commands["!clearbirthday"] = clear_birthday
commands["!rlstats"] = get_rl_rank
commands["!getrlrank"] = get_rl_rank
commands["!rlrank"] = get_rl_rank
commands["!mybirthday"] = my_birthday
commands["!setbirthday"] = set_birthday
commands["!roll"] = roll
commands["!broadcast"] = broadcast

# Audio commands
commands["!tts"] = text_to_speech
commands["!say"] = text_to_speech
commands["!volume"] = volume
commands["!sv"] = volume
commands["!stop"] = stop
commands["!s"] = stop
commands["!stahp"] = stop
commands["!stap"] = stop
commands["!pause"] = pause
commands["!pa"] = pause
commands["!resume"] = resume
commands["!r"] = resume
commands["!delete"] = delete
commands["!d"] = delete
commands["!remove"] = delete
commands["!skip"] = skip
commands["!sk"] = skip
commands["!q"] = queue_page
commands["!queue"] = queue_page
commands["!next"] = next
commands["!n"] = next
commands["!vote"] = vote
commands["!v"] = vote
commands["!queuepage"] = queue_page
commands["!summon"] = summon
commands["!lock"] = summon
commands["!unsummon"] = unsummon
commands["!desummon"] = unsummon
commands["!release"] = unsummon
commands["!repeat"] = repeat
commands["!again"] = repeat
commands["!a"] = repeat
commands["!shuffle"] = shuffle
commands["!sh"] = shuffle

# Intro commands
commands["!introstop"] = introstop
commands["!stopintro"] = introstop
commands["!is"] = introstop
commands["!intro"] = intro
commands["!i"] = intro
commands["!myintros"] = myintros
commands["!intros"] = myintros
commands["!mi"] = myintros
commands["!deleteintro"] = deleteintro
commands["!introdelete"] = deleteintro
commands["!di"] = deleteintro
commands["!upload"] = upload
commands["!up"] = upload
commands["!u"] = upload

# Default intro commands
commands["!defaultintro"] = default_intro
commands["!di"] = default_intro
commands["!defaultintros"] = list_default_intros
commands["!dis"] = list_default_intros
commands["!ldi"] = list_default_intros
commands["!deletedefaultintro"] = delete_default_intro
commands["!ddi"] = delete_default_intro
commands["!uploaddefaultintro"] = upload_default_intro
commands["!udi"] = upload_default_intro

# Wow commands
commands["!playername"] = playername
commands["!lastraidplayer"] = lastraid_player
commands["!lastraid"] = lastraid_player
commands["!lastraidguild"] = lastraid_guild

async def slot(message, bot_channel, client):
    await client.delete_message(message)
    if message.channel != bot_channel:
        await client.send_message(message.channel, '{}: Check bot-spam for the result!'.format(message.author.name))
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

    if first_column[1] is second_column[1] is third_column[1]:
        result = "Congratulations, you won!"
    else:
        result = "Sorry, but you lost..."
    slot_string = "  {}{}{}\n>{}{}{}<\n  {}{}{}\n\n{}".format(first_column[0], second_column[0], third_column[0],
                                                            first_column[1], second_column[1], third_column[1],
                                                            first_column[2], second_column[2], third_column[2], result)
    await client.send_message(bot_channel, '{}: Good luck!\n\n{}'.format(message.author.name, slot_string))

commands["!slot"] = slot
commands["!spin"] = slot

async def joined(message, bot_channel, client):
    await client.delete_message(message)
    await client.send_message(bot_channel, '{}: You joined the Ohm server {}!'.format(message.author.name,
                                                                                      message.author.joined_at))

commands["!joined"] = joined


async def suggest(message, bot_channel, client):
    suggestion = message.content[9:]
    if len(suggestion) < 3:
        await client.send_message(bot_channel,
                                  "{}: Please suggest something proper.".format(message.author.mention))
        return
    server = get_server(message.server)
    member = server.get_member(message.author.id)
    suggestion_loc = 'suggestions.txt'.format(server.server_loc, member.member_loc)
    with open(suggestion_loc, 'a') as f:
        f.write("Suggestion from {} on server {}:\n{}\n".format(message.author, message.server, suggestion))
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

async def leave(message, bot_channel, client):
    await client.delete_message(message)
    server = get_server(message.server)
    server.split_list.remove(message.author)
    await client.send_message(bot_channel,
                              '{}: You have left the queue!\n'
                              'Current queue: {}'.format(message.author.mention, server.print_queue()))

async def team(message, bot_channel, client):
    subcommands = {
        "join": join,
        "leave": leave
    }
    parameters = message.content.lower().split()
    # Check if there are subcommands.
    if len(parameters) > 1:
        if parameters[1] in subcommands:
            await subcommands[parameters[1]](message, bot_channel, client)


commands["!team"] = team


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
commands["!gbi"] = get_bot_invite

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
    try:
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
    finally:
        lock.release()

commands["!playbuttons"] = playbuttons

async def sharedgames(message, bot_channel, client):
    await client.delete_message(message)
    content = message.content.split()
    users = content[1:]
    api_interface = steamapi.core.APIConnection(api_key="BDCD48F7FF3046773D26D94F742B0B54", validate_key=True)

    class SharedGame:
        def __init__(self, game):
            self.game = game
            self.total_playtime_forever = game.playtime_forever

        def add_together_playtime(self, game):
            self.total_playtime_forever += game.playtime_forever
            return self

    sharedgames_list = list()
    first_injection = True
    user_string = str()
    print("Starting user game list retrieval...")
    start = time.time()
    for user in users:
        try:
            steam_user = steamapi.user.SteamUser(userurl=user)
        except steamapi.errors.UserNotFoundError:
            continue
        user_string += "**{}**, ".format(steam_user.name)
        games = steam_user.games
        if first_injection:
            sharedgames_list = list(map(lambda game: SharedGame(game), games))
            first_injection = False
        else:
            sharedgames_list = list(filter(lambda shared_game: shared_game.game in games, sharedgames_list))
            sharedgames_list = list(map(lambda shared_game: shared_game.add_together_playtime(games[games.index(shared_game.game)]), sharedgames_list))
    print("Done! It took {} seconds.".format(time.time()-start))
    if first_injection:
        await client.send_message(bot_channel, "Sorry, could not find any users...")
        return
    print("Starting game info retrieval...")
    start = time.time()
    print_string = str()
    cnt = 1
    sharedgames_list_temp = list()

    def games_filter(shared_game):
        url = urllib.request.urlopen("http://store.steampowered.com/app/{}".format(shared_game.game.appid)).read().decode('utf-8')
        if re.search(">Multi-player</a>", url) or re.search(">Co-op</a>", url):
            sharedgames_list_temp.append(shared_game)
    thread_list = list()
    for game in sharedgames_list:
        thread = threading.Thread(target=games_filter, args=[game])
        thread.start()
        thread_list.append(thread)
    for thread in thread_list:
        thread.join()
    sharedgames_list = sharedgames_list_temp
    sharedgames_list = sorted(sharedgames_list, key=lambda shared_game: shared_game.total_playtime_forever, reverse=True)
    print("Done! It took {} seconds.".format(time.time()-start))
    for shared_game in sharedgames_list:
        print_string += "{}. {}   **{} hours total**\n".format(cnt, shared_game.game.name, math.ceil(shared_game.total_playtime_forever/60))
        cnt += 1
        if cnt == 40:
            break
    await client.send_message(bot_channel, "{} share these games:\n{}".format(user_string[:-2], print_string))

commands["!sharedgames"] = sharedgames
commands["!move"] = move

async def on_reaction_add(reaction, user):
    server = get_server(reaction.message.server)
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
    server = get_server(after.server)
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
    server = get_server(server)
    for task in server.playlist.task_list:
        task.cancel()
    server_list.remove(server)


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
