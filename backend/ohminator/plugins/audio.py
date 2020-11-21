import math
import os
import random
import time
import traceback
from tempfile import mkstemp

import youtube_dl
from gtts import gTTS
from utils import RegisterCommand, get_server

import utils
import discord
import asyncio


async def connect_to_voice_channel(message, client, db_guild, plugin, voice_channel=None):
    channel = voice_channel if voice_channel else message.author.voice_channel
    voice_client = client.voice_client_in(message.author.server)
    if voice_client:
        await voice_client.disconnect()
    voice_client = await client.join_voice_channel(channel)


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












@RegisterCommand("vote", "v")
async def vote(message, client, db_guild, plugin):
    await message.delete()
    server = ohminator.utils.get_server(message.guild)
    parameters = message.content.split()
    try:
        index = int(parameters[1]) - 1
    except ValueError:
        await message.channel.send(f'{message.author.name}: Please give a numeric value!')
        return
    except IndexError:
        await message.channel.send(f'{message.author.name}: Please give an index to vote for!')
        return

    try:
        playlist_element = server.playlist.yt_playlist[index]
        if message.author.id in playlist_element.vote_list:
            await message.channel.send(f'{message.author.name}: You can only vote once on one entry!')
            return
        playlist_element.vote_list.append(message.author.id)
        for element in server.playlist.yt_playlist:
            if len(element.vote_list) < len(playlist_element.vote_list):
                server.playlist.yt_playlist.remove(playlist_element)
                server.playlist.yt_playlist.insert(server.playlist.yt_playlist.index(element), playlist_element)
                break
        await message.channel.send(f'{message.author.name}: {playlist_element.title} has been voted for!')

    except IndexError:
        await message.channel.send(f'{message.author.name}: Index {index+1} is out of queue bounds!')


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


@RegisterCommand("queue", "q", "queuepage")
async def queue_page(message, client, db_guild, plugin):
    await message.delete()
    server = ohminator.utils.get_server(message.guild)
    if len(server.playlist.yt_playlist) == 0:
        await message.channel.send(f'{message.author.name}: There is nothing in the queue!')
        return
    parameters = message.content.split()
    try:
        index = int(parameters[1]) - 1
        if not 0 <= index < len(server.playlist.yt_playlist):
            await message.channel.send(f'{message.author.name}: Index {index + 1} is out of queue bounds!')
        else:
            await print_from_index(index, server, message, client)
    except ValueError:
        await message.channel.send(f'{message.author.name}: Please give a numeric value!')
    except IndexError:
        server.queue_pages = QueuePage(server)
        await server.queue_pages.print_next_page(client, message.channel)


@RegisterCommand("yttop", "playtop", "pt")
async def play_on_top(message, client, db_guild, plugin):
    server = ohminator.utils.get_server(message.guild)
    await play_from_internet(message, client, db_guild, plugin=plugin)
    # If the queue is not empty, the last entry must be what was added last.
    # It should not be a race condition as we're not awaiting anything.
    if server.playlist.yt_playlist:
        server.playlist.yt_playlist.insert(0, server.playlist.yt_playlist.pop())





async def print_from_index(index, server, message, client):
    play = server.playlist.yt_playlist
    queue = str()
    try:
        for i in range(index, index + 30, 1):
            votes = ''
            if len(play[i].vote_list) > 0:
                votes = f' **[{len(play[i].vote_list)}]**'
            queue += f"{i + 1}: {play[i].title}{votes}\n"
        queue += f"Total entries: {len(play)}\n"
    except IndexError:
        queue += "End of queue!"
    await message.channel.send(message.channel.send(f'{message.author.name}: '
                                                   f'Here is the current queue from index {index+1}:\n{queue.strip()}'))


class QueuePage:
    def __init__(self, server):
        self.page_num = 0
        self.server = server
        self.message = None
        self.end = False

    async def print_next_page(self, client, channel):
        if self.end:
            return
        play = self.server.playlist.yt_playlist
        queue = str()
        try:
            for i in range(self.page_num*30, (self.page_num*30)+30, 1):
                votes = ''
                if len(play[i].vote_list) > 0:
                    votes = f' **[{len(play[i].vote_list)}]**'
                queue += f"{i+1}: {play[i].title}{votes}\n"

            pages_left = math.ceil((len(play)-((self.page_num*30)+29))/30)
            queue += f"Total entries: {len(play)}\n"
            if pages_left > 0:
                queue += f"There {pages_left == 1 and 'is' or 'are'} {pages_left} " \
                         f"{pages_left == 1 and 'page' or 'pages'} left"
        except IndexError:
            queue += "End of queue!"
            self.end = True

        self.page_num += 1
        if self.message is None:
            self.message = await channel.send(f'Here is the current queue:\n{queue.strip()}')
        else:
            await self.message.edit(f'Here is the current queue:\n{queue.strip()}')


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
