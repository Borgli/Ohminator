import discord
import asyncio
import youtube_dl
import threading
import urllib.request
import os
import random
import time


class Ohminator:
    current_voice = None
    active_player = None
    intro_names = {'runarl', 'Rune', 'Chimeric', 'Johngel', 'Christian Berseth',
                   'Jan Ivar Ugelstad', 'Christian F. Vegard', 'Martin', 'Kristoffer Skau', 'Ginker'}
    black_list = {'Christian Berseth', 'Chimeric', 'Johngel'}
    yt_lock = threading.RLock()
    yt_cooldown = time.time()

class Stats:
    total_time_spent = None
    time_in_channels = dict()
    msg_count = 0
    def __init__(self):
        stats_file = open('ohmstats', 'wb+')
        self.msg_count = int(stats_file.readline())
        stats_file.readline()
        channel_stats = stats_file.readline()
        while channel_stats != '## Channel Stats ##':
            self.time_in_channels[channel_stats.rfind()]


class OhmUser(discord.User):
    def __init__(self, member):
        super(OhmUser, self).__init__()
        self.member = member
        self.stats = Stats()

client = discord.Client()
ohm = Ohminator()


@client.event
async def on_server_join(server):
    discord.utils.get(client.get_all_members(), )


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    """if message.content.startswith('!test'):
        counter = 0
        tmp = await client.send_message(message.channel, 'Calculating messages...')
        async for log in client.logs_from(message.channel, limit=100):
            if log.author == message.author:
                counter += 1

        await client.edit_message(tmp, 'You have {} messages.'.format(counter))
    elif message.content.startswith('!sleep'):
        await asyncio.sleep(5)
        await client.send_message(message.channel, 'Done sleeping')
    """
    if message.content.startswith('!yt'):
        link = message.content[4:]
        if message.author.voice_channel is None:
            await client.delete_message(message)
            await client.send_message(message.channel, '{}: Please join a voice channel to play your link!'.format(message.author.name))
            return

        if message.author.is_afk:
            await client.delete_message(message)
            return

        if time.time() - ohm.yt_cooldown < 2:
            await client.send_message(message.channel, '{}: A link was just posted. Please wait a moment before trying again!'.format(message.author.name))
            await client.delete_message(message)
            return
        ohm.yt_cooldown = time.time()

        if ohm.current_voice is None:
            ohm.current_voice = await client.join_voice_channel(message.author.voice_channel)
        elif ohm.current_voice.channel != message.author.voice_channel:
            await ohm.current_voice.disconnect()
            ohm.current_voice = await client.join_voice_channel(message.author.voice_channel)

        await client.delete_message(message)
        if ohm.active_player is not None and ohm.active_player.is_playing():
            await client.send_message(message.channel, '{}: Something is already playing!'.format(message.author.name))
            return

        try:
            ohm.active_player = await ohm.current_voice.create_ytdl_player(link)
            await client.send_message(message.channel, '{}: \nNow playing: {}\nIt is {} seconds long'.format(message.author.name, ohm.active_player.title, ohm.active_player.duration))
            ohm.active_player.start()
        except:
            await client.send_message(message.channel, '{}: Your link could not be played!'.format(message.author.name))

    elif message.content.startswith('!stahp') or message.content.startswith('!stop'):
        await client.delete_message(message)
        if ohm.active_player is None or not ohm.active_player.is_playing:
            await client.send_message(message.channel, '{}: No active player!'.format(message.author.name))
        else:
            await client.send_message(message.channel, '{} stopped the player!'.format(message.author.name))
            ohm.active_player.stop()

    elif message.content.startswith('!help') or message.content.startswith('!commands'):
        await client.delete_message(message)
        await client.send_message(message.channel,
                                  '{}: List of commands: \n'
                                  '!help or !command\t-\tPrints out this menu.\n'
                                  '!yt [youtube link]\t\t-\tPlays audio from YouTube in voice channel of caller.\n'
                                  '!stahp\t\t\t\t\t\t-\tStops any playing sound.\n'
                                  '!joined\t\t\t\t\t\t-\tTells you when you joined Ohm!\n'
                                  '!roll [lowest] [highest]\t\t\t\t\t-\tRoll a number between lowest and highest'.format(message.author.name))

    elif message.content.startswith('!ohminator'):
        await client.delete_message(message)
        await client.send_message(message.channel, 'I am the Ohminator, bleep, bloop! Type !help to see a list of '
                                                   'commands!')

    elif message.content.startswith('!roll'):
        try:
            options = message.content.split()
            rand = random.randint(int(options[1]), int(options[2]))
            await client.send_message(message.channel,'{}: You rolled {}!'.format(message.author.name, rand))
        except:
            await client.send_message(message.channel, '{}: Could not roll with those parameters!'.format(message.author.name))

    elif message.content.startswith('!joined'):
        await client.delete_message(message)
        await client.send_message(message.channel, '{}: You joined the Ohm server {}!'.format(message.author.name, message.author.joined_at))

    elif message.content.startswith('!stream'):
        link = message.content[8:]

        if message.author.voice_channel is None:
            await client.delete_message(message)
            await client.send_message(message.channel,
                                      '{}: Please join a voice channel to play your link!'.format(message.author.name))
            return

        if message.author.is_afk:
            return

        if ohm.current_voice is None:
            ohm.current_voice = await client.join_voice_channel(message.author.voice_channel)
        elif ohm.current_voice.channel != message.author.voice_channel:
            await ohm.current_voice.disconnect()
            ohm.current_voice = await client.join_voice_channel(message.author.voice_channel)

        await client.delete_message(message)
        if ohm.active_player is not None and ohm.active_player.is_playing():
            await client.send_message(message.channel, '{}: Something is already playing!'.format(message.author.name))
            return

        try:
            file_name, header = urllib.request.urlretrieve(link)
            ohm.active_player = ohm.current_voice.create_ffmpeg_player(file_name)
            await client.send_message(message.channel,
                                      '{}: \nNow playing your link!\n'.format(message.author.name))
            ohm.active_player.start()

        except:
            await client.send_message(message.channel, '{}: Your link could not be played!'.format(message.author.name))

    elif message.content.startswith('!troll'):
        link = message.content[7:]
        if message.author.voice_channel is not None:
            await client.delete_message(message)
            await client.send_message(message.channel,
                                      '{}: You are using this command wrong!'.format(message.author.name))
            return

        if message.author.is_afk:
            return

        if ohm.current_voice is None:
            ohm.current_voice = await client.join_voice_channel(message.author.voice_channel)
        elif ohm.current_voice.channel != message.author.voice_channel:
            await ohm.current_voice.disconnect()
            ohm.current_voice = await client.join_voice_channel(message.author.voice_channel)

        await client.delete_message(message)
        if ohm.active_player is not None and ohm.active_player.is_playing():
            await client.send_message(message.channel, '{}: Something is already playing!'.format(message.author.name))
            return

        try:
            ohm.active_player = await ohm.current_voice.create_ytdl_player(link)
            await client.send_message(message.channel,
                                      '{}: \nNow playing: {}\nIt is {} seconds long'.format(message.author.name,
                                                                                            ohm.active_player.title,
                                                                                            ohm.active_player.duration))
            ohm.active_player.start()
        except:
            await client.send_message(message.channel, '{}: Your link could not be played!'.format(message.author.name))

    elif message.content.startswith('!stahp') or message.content.startswith('!stop'):
        await client.delete_message(message)
        if ohm.active_player is None or not ohm.active_player.is_playing:
            await client.send_message(message.channel, '{}: No active player!'.format(message.author.name))
        else:
            await client.send_message(message.channel, '{} stopped the player!'.format(message.author.name))
            ohm.active_player.stop()


@client.event
async def on_voice_state_update(before, after):
    if after.voice_channel is None or after.is_afk:
        return
    if before.name is not None and before.name in ohm.intro_names \
            and before.voice_channel != after.voice_channel:
        if after.voice_channel.name != 'Supreme Ohhhhhmmmmmmm':
            for member in after.voice_channel.voice_members:
                if member.name in ohm.black_list:
                    return

        if ohm.current_voice is None:
            ohm.current_voice = await client.join_voice_channel(after.voice_channel)

        elif ohm.current_voice.channel != after.voice_channel:
            await ohm.current_voice.disconnect()

            if after.voice_channel is not None:
                try:
                    ohm.current_voice = await client.join_voice_channel(after.voice_channel)
                except:
                    return
            else:
                return

        if ohm.active_player is not None and ohm.active_player.is_playing():
            ohm.active_player.stop()

        try:
            if before.name == 'runarl':
                ohm.active_player = ohm.current_voice.create_ffmpeg_player('runarl/sjabling.wav')
            elif before.name == 'Johngel':
                ohm.active_player = ohm.current_voice.create_ffmpeg_player('Christer/Christer.wav')
            elif before.name == 'Chimeric':
                ohm.active_player = ohm.current_voice.create_ffmpeg_player('Marius/MarijusJingjeee.wav')
            elif before.name == 'Christian Berseth':
                ohm.active_player = ohm.current_voice.create_ffmpeg_player('Christian Berseth/last_one_niggu.wav')
            elif before.name == 'Jan Ivar Ugelstad':
                ohm.active_player = ohm.current_voice.create_ffmpeg_player('Jan Ivar Ugelstad/discord EEEEEEE.wav')
            elif before.name == 'Christian F. Vegard':
                ohm.active_player = ohm.current_voice.create_ffmpeg_player('Christian F. Vegard/ChristianVJingle.wav')
            elif before.name == 'Martin':
                ohm.active_player = ohm.current_voice.create_ffmpeg_player('Martin/MartinHathJing.wav')
            elif before.name == 'Kristoffer Skau':
                ohm.active_player = ohm.current_voice.create_ffmpeg_player('Kristoffer Skau/SpaceDanceJingleMOARBASS.wav')
            else:
                ohm.active_player = ohm.current_voice.create_ffmpeg_player('Rune/Bee_Gees_walk.wav')
            ohm.active_player.start()
        except Exception as e:
            print(e)

@client.event
async def on_member_update(before, after):
    if (before.game is None or before.game.name != 'Rocket League') and (after.game is not None and after.game.name == 'Rocket League'):
        if after.voice_channel is None or after.is_afk:
            return

        if after.voice_channel.name != 'Supreme Ohhhhhmmmmmmm':
            for member in after.voice_channel.voice_members:
                if member.name in ohm.black_list:
                    return

        if ohm.current_voice is None:
            ohm.current_voice = await client.join_voice_channel(after.voice_channel)

        elif ohm.current_voice.channel != after.voice_channel:
            await ohm.current_voice.disconnect()

            if after.voice_channel is not None:
                try:
                    ohm.current_voice = await client.join_voice_channel(after.voice_channel)
                except:
                    return

            else:
                return

        if ohm.active_player is not None and ohm.active_player.is_playing():
            return

        try:
            ohm.active_player = ohm.current_voice.create_ffmpeg_player('WhatRocketLeague.wav')
            ohm.active_player.start()
        except Exception as e:
            print(e)

client.run('MTc2NDMzMTMwMzM1NTAyMzM3.CgvoFg.FLaupAZZ5OviZ1Fb7gAO_Aq-sLo')
