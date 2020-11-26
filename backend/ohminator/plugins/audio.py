import math
import os
import random
import time
import traceback
from tempfile import mkstemp

import youtube_dl
from gtts import gTTS
from utils import RegisterCommand

import utils
import discord
import asyncio


@RegisterCommand("summon", "lock", "acquire")
async def summon(message, client, db_guild, plugin):
    await message.delete()
    parameters = message.content.split()
    server = ohminator.utils.get_server(message.guild)
    # If there's a parameter it should be the channel you want the bot locked to
    if len(parameters) > 1:
        try:
            # TODO: Fix this.
            channel = server.get_channel(parameters[1])
            if channel.type == discord.ChannelType.voice:
                server.playlist.summoned_channel = channel.discord_channel
                await connect_to_voice_channel(message, client, db_guild, plugin, voice_channel=channel.discord_channel)
                await message.channel.send(f"{message.author.name}: Locked to channel {channel.name}")
            else:
                await message.channel.send(f"{message.author.name}: "
                                           f"That channel is a text channel, not a voice channel.\n"
                                           "Usage: !summon [(channel id or name)]")
        except ohminator.utils.NoChannelFoundError:
            await message.channel.send(f"{message.author.name}: "
                                       f"Couldn\'t find a channel matching the parameter!\n"
                                       "Usage: !summon [(channel id or name)]")
    else:
        if message.author.voice.voice_channel:
            server.playlist.summoned_channel = message.author.voice.voice_channel
            await connect_to_voice_channel(message, client, db_guild, plugin)
            await message.channel.send(f"{message.author.name}: Locked to channel "
                                       f"{message.author.voice.voice_channel.name}")
        else:
            await message.channel.send(f"{message.author.name}: You must be in a voice channel "
                                       "to use this command without a channel id.\n"
                                       "Usage: !summon [(channel id)]")


@RegisterCommand("unsummon", "desummon", "release")
async def unsummon(message, client, db_guild, plugin):
    await message.delete()
    server = ohminator.utils.get_server(message.guild)
    await message.channel.send(f"{message.author.name}: Released from channel {server.playlist.summoned_channel.name}")
    server.playlist.summoned_channel = None





@RegisterCommand("playbuttons")
async def playbuttons(message, client, db_guild, plugin):
    await message.delete()
    server = get_server(message.guild)
    lock = asyncio.locks.Lock()
    await lock.acquire()
    try:
        await message.channel.send('Here are buttons for controlling the playlist.\nUse reactions to trigger them!')
        play = await message.channel.send('Play :arrow_forward:')
        pause = await message.channel.send('Pause :pause_button:')
        stop = await message.channel.send('Stop :stop_button:')
        next = await message.channel.send('Next song :track_next:')
        volume_up = await message.channel.send('Volume up :heavy_plus_sign:')
        volume_down = await message.channel.send('Volume down :heavy_minus_sign:')
        queue = await message.channel.send('Current queue :notes:')
        await message.channel.send('----------------------------------------')
        server.playbuttons = PlayButtons(play, pause, stop, next, volume_up, volume_down, queue)
    finally:
        lock.release()


class PlayButtons:
    def __init__(self, play, pause, stop, next_track, volume_up, volume_down, queue):
        self.play = play
        self.pause = pause
        self.stop = stop
        self.next_track = next_track
        self.volume_up = volume_up
        self.volume_down = volume_down
        self.queue = queue

    async def handle_message(self, message, server, client):
        if server.active_player is None:
            return
        try:
            if message.id == self.play.id:
                server.active_player.resume()
            elif message.id == self.pause.id:
                server.active_player.pause()
            elif message.id == self.stop.id:
                server.playlist.yt_playlist.clear()
                server.active_player.stop()
            elif message.id == self.next_track.id:
                server.active_player.stop()
            elif message.id == self.queue.id:
                cnt = 1
                queue = str()
                more_entries = False
                for play in server.playlist.yt_playlist:
                    if cnt <= 30:
                        queue += f"{cnt}: {play.title}\n"
                    else:
                        more_entries = True
                    cnt += 1
                if more_entries is True:
                    if cnt - 30 == 1:
                        entry = 'entry'
                    else:
                        entry = 'entries'
                    queue += f"And {cnt - 30} {entry} more..."
                await message.channel.send(f'Here is the current queue:\n{queue.strip()}')
            elif message.id == self.volume_up.id:
                if not server.active_player.source.volume > 1.8:
                    server.active_player.source.volume += 0.2
            elif message.id == self.volume_down.id:
                if not server.active_player.source.volume < 0.2:
                    server.active_player.source.volume -= 0.2
        except:
            traceback.print_exc()


@RegisterCommand("fixaudio")
async def fix_audio(message, client, db_guild, plugin):
    if message.guild.voice_client:
        await message.guild.voice_client.disconnect()
    await message.channel.send(f"{message.author.name}: Audio should now be functional again. "
                               f"If problem persists, please contact the developer or post an issue at "
                               f"https://github.com/Borgli/Ohminator/issues")
