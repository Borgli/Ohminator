import math
import os
import random
import time
import traceback
from tempfile import mkstemp

import youtube_dl
from gtts import gTTS
from ohminator.utils import RegisterCommand, get_server

import ohminator.utils
import discord
import asyncio


@RegisterCommand("tts", "say")
async def text_to_speech(message, bot_channel, client):
    await client.delete_message(message)
    text = message.content[5:]
    server = ohminator.utils.get_server(message.server)
    if not server.next_tts_created:
        client.loop.create_task(play_next_tts(server, client))
        server.next_tts_created = True
    await server.playlist.playlist_lock.acquire()
    if message.author.voice_channel is None or message.author.voice.is_afk:
        await client.send_message(bot_channel, f'{message.author.name}: '
                                               f'Please join a voice channel to use text-to-speech!')
        return
    try:

        if len(server.tts_queue) > 0 or (server.active_tts is not None and server.active_tts.is_playing()):
            server.tts_queue.append(text)
            return

        if (server.intro_player is not None and server.intro_player.is_playing()) or (server.active_player is not None
            and (not server.active_player.is_done() or server.active_player.is_playing())):
            server.tts_queue.clear()
            return
        try:
            server.settings.update_settings(server.db.Servers, {"_id": server.id})
            tts = gTTS(text=text, lang=server.settings.tts_language)
        except:
            traceback.print_exc()
            await client.send_message(bot_channel,
                                      f'{message.author.name}: Language setting is not a valid setting! Please fix.')
            return

        # Handles playing intros when the bot is summoned
        if server.playlist.summoned_channel:
            if message.author.voice.voice_channel == server.playlist.summoned_channel:
                voice_channel = server.playlist.summoned_channel
            else:
                await client.send_message(bot_channel,
                                          f'{message.author.name}: '
                                          f'The bot is locked to channel {server.playlist.summoned_channel.name}. '
                                          'Please join that channel to use !tts.')
                return
        else:
            voice_channel = message.author.voice_channel

        voice_client = await ohminator.utils.connect_to_voice(client, message.author.server, voice_channel)

        fd, filename = mkstemp()

        def after_tts():
            if server.active_tts.error:
                print(server.active_tts.error)
                traceback.print_exc()
            client.loop.call_soon_threadsafe(server.next_tts.set)
            os.remove(filename)

        tts.save(filename)
        server.active_tts = voice_client.create_ffmpeg_player(filename, after=after_tts)
        server.active_tts.start()
    finally:
        server.playlist.playlist_lock.release()


async def play_next_tts(server, client):
    while not client.is_closed:
        await server.next_tts.wait()
        await server.playlist.playlist_lock.acquire()
        try:
            if (server.intro_player is not None and server.intro_player.is_playing()) or (server.active_player is not None
                    and (not server.active_player.is_done() or server.active_player.is_playing())):
                        server.tts_queue.clear()
            else:
                if len(server.tts_queue) > 0:
                    something_to_play = False
                    while True:
                        if len(server.tts_queue) <= 0:
                            break
                        text = server.tts_queue.pop(0)
                        try:
                            server.settings.update_settings(server.db.Servers, {"_id": server.id})
                            tts = gTTS(text=text, lang=server.settings.tts_language)
                        except:
                            continue

                        fd, filename = mkstemp()

                        def after_tts():
                            server.tts_queue.pop(0)
                            client.loop.call_soon_threadsafe(server.next_tts.set)
                            os.remove(filename)

                        tts.save(filename)
                        voice_client = client.voice_client_in(server.discord_server)
                        server.active_tts = voice_client.create_ffmpeg_player(filename, after=after_tts)
                        if server.active_tts:
                            something_to_play = True
                            break
                    if something_to_play:
                        server.active_tts.start()
        finally:
            server.next_tts.clear()
            server.playlist.playlist_lock.release()


async def connect_to_voice_channel(message, bot_channel, client, voice_channel=None):
    channel = voice_channel if voice_channel else message.author.voice_channel
    voice_client = client.voice_client_in(message.author.server)
    if voice_client:
        await voice_client.disconnect()
    voice_client = await client.join_voice_channel(channel)


@RegisterCommand("summon", "lock", "acquire")
async def summon(message, bot_channel, client):
    await client.delete_message(message)
    parameters = message.content.split()
    server = ohminator.utils.get_server(message.server)
    # If there's a parameter it should be the channel you want the bot locked to
    if len(parameters) > 1:
        try:
            channel = server.get_channel(parameters[1])
            if channel.type == discord.ChannelType.voice:
                server.playlist.summoned_channel = channel.discord_channel
                await connect_to_voice_channel(message, bot_channel, client, voice_channel=channel.discord_channel)
                await client.send_message(bot_channel, f"{message.author.name}: Locked to channel {channel.name}")
            else:
                await client.send_message(bot_channel, f"{message.author.name}: "
                                                       f"That channel is a text channel, not a voice channel.\n"
                                                       "Usage: !summon [(channel id or name)]")
        except ohminator.utils.NoChannelFoundError:
            await client.send_message(bot_channel, f"{message.author.name}: "
                                                   f"Couldn\'t find a channel matching the parameter!\n"
                                                   "Usage: !summon [(channel id or name)]")
    else:
        if message.author.voice.voice_channel:
            server.playlist.summoned_channel = message.author.voice.voice_channel
            await connect_to_voice_channel(message, bot_channel, client)
            await client.send_message(bot_channel, f"{message.author.name}: Locked to channel "
                                                   f"{message.author.voice.voice_channel.name}")
        else:
            await client.send_message(bot_channel, f"{message.author.name}: You must be in a voice channel "
                                                   "to use this command without a channel id.\n"
                                                   "Usage: !summon [(channel id)]")


@RegisterCommand("unsummon", "desummon", "release")
async def unsummon(message, bot_channel, client):
    await client.delete_message(message)
    server = ohminator.utils.get_server(message.server)
    await client.send_message(bot_channel, f"{message.author.name}: "
                                           f"Released from channel {server.playlist.summoned_channel.name}")
    server.playlist.summoned_channel = None


@RegisterCommand("volume", "sv")
async def volume(message, bot_channel, client):
    await client.delete_message(message)
    server = ohminator.utils.get_server(message.server)
    if server.active_player is None or server.active_player.is_done():
        await client.send_message(bot_channel, f'{message.author.name}: Nothing is playing!')
    else:
        parameters = message.content.split()
        if len(parameters) < 2:
            current_volume = server.active_player.volume
        else:
            try:
                current_volume = float(parameters[1])/2/100.0
            except ValueError:
                await client.send_message(bot_channel, f'{message.author.name}: Please give a numeric value!')
                return

        if current_volume <= 0.0:
            icon = ':mute:'
        elif 0.0 < current_volume < 0.15:
            icon = ':speaker:'
        elif 0.14 < current_volume < 0.35:
            icon = ':sound:'
        else:
            icon = ':loud_sound:'

        if len(parameters) < 2:
            await client.send_message(bot_channel, f'{icon}: {message.author.name}, '
                                                   f'the volume for the current track is '
                                                   f'{int(current_volume*2*100.0)}%!')
        elif parameters[1] == current_volume:
            await client.send_message(bot_channel, f'{icon}: {message.author.name}, '
                                                   f'the volume is already the given value!')
        else:
            if current_volume < 0.0:
                current_volume = 0.0
            elif current_volume > 0.5:
                current_volume = 0.5

            await client.send_message(bot_channel, f'{icon}: {message.author.name}, the volume was changed from '
                                                   f'{int(server.active_player.volume*2*100.0)}% to '
                                                   f'{int(current_volume*2*100.0)}%!')
            server.active_player.volume = current_volume


@RegisterCommand("stop", "s", "stahp", "stap")
async def stop(message, client, db_guild, plugin):
    await message.delete()
    server = ohminator.utils.get_server(message.guild)
    if server.active_player is None or not message.guild.voice_client.is_playing():
        await message.channel.send(f'{message.author.name}: No active player to stop!')
    else:
        await message.channel.send(f':stop_button:: {message.author.name} stopped the player and cleared the queue!')
        server.playlist.yt_playlist.clear()
        message.guild.voice_client.stop()


@RegisterCommand("pause", "pa")
async def pause(message, bot_channel, client):
    await client.delete_message(message)
    server = ohminator.utils.get_server(message.server)
    if server.active_player is None:
        await client.send_message(bot_channel, f'{message.author.name}: Nothing to pause!')
    elif not server.active_player.is_playing():
        await client.send_message(bot_channel, f'{message.author.name}: The player is not playing because it was '
                                               f'stopped or is already paused!')
    else:
        await client.send_message(bot_channel, f':pause_button:: {message.author.name} paused the player!')
        server.active_playlist_element.pause_time = time.time()
        server.active_player.pause()


@RegisterCommand("resume", "r")
async def resume(message, bot_channel, client):
    await client.delete_message(message)
    server = ohminator.utils.get_server(message.server)
    if server.active_player is None or server.active_player.is_done():
        await client.send_message(bot_channel, f'{message.author.name}: Nothing to resume!')
    else:
        await client.send_message(bot_channel, f':arrow_forward:: {message.author.name} resumed the player!')
        server.active_playlist_element.start_time += (server.active_playlist_element.pause_time-server.active_playlist_element.start_time)
        server.active_player.resume()


@RegisterCommand("repeat", "again", "a")
async def repeat(message, bot_channel, client):
    await client.delete_message(message)
    server = ohminator.utils.get_server(message.server)
    if server.active_player is None or not server.active_player.is_playing():
        await client.send_message(bot_channel, f'{message.author.name}: Nothing to repeat!')
    else:
        await client.send_message(bot_channel,
                                  f':repeat: {message.author.name} repeated {server.active_playlist_element.title}.')
        server.playlist.yt_playlist.insert(0, server.active_playlist_element)


@RegisterCommand("shuffle", "sh")
async def shuffle(message, bot_channel, client):
    await client.delete_message(message)
    server = ohminator.utils.get_server(message.server)
    if server.active_player is None or not server.active_player.is_playing():
        await client.send_message(bot_channel, f'{message.author.name}: Nothing to shuffle!')
    else:
        await client.send_message(bot_channel,
                                  f':twisted_rightwards_arrows: {message.author.name} shuffled the list.')
        random.shuffle(server.playlist.yt_playlist)
        server.playlist.yt_playlist.sort(key=lambda element: len(element.vote_list), reverse=True)


@RegisterCommand("delete", "d", "remove")
async def delete(message, bot_channel, client):
    await client.delete_message(message)
    server = ohminator.utils.get_server(message.server)
    parameters = message.content.split()
    try:
        index = int(parameters[1]) - 1
    except ValueError:
        await client.send_message(bot_channel, f'{message.author.name}: Please give a numeric value!')
        return
    except IndexError:
        await client.send_message(bot_channel, f'{message.author.name}: Please give an index to delete!')
        return

    try:
        playlist_element = server.playlist.yt_playlist[index]
        server.playlist.yt_playlist.remove(playlist_element)
        await client.send_message(bot_channel, f"{message.author.name}: Entry \'{playlist_element.title}\' "
                                               f"with index {index+1} was deleted from the queue.")
    except IndexError:
        await client.send_message(bot_channel, f'{message.author.name}: Index {index+1} is out of queue bounds!')


@RegisterCommand("skip", "sk")
async def skip(message, bot_channel, client):
    await client.delete_message(message)
    server = ohminator.utils.get_server(message.server)
    await server.playlist.playlist_lock.acquire()
    try:
        if server.active_player is None and len(server.playlist.yt_playlist) > 0:
            await client.send_message(bot_channel, f'{message.author.name}: Nothing to skip!')
        else:
            await client.send_message(bot_channel, f':track_next:: {message.author.name} skipped the song!')
            server.active_player.stop()
    finally:
        server.playlist.playlist_lock.release()


@RegisterCommand("next", "n")
async def next(message, bot_channel, client):
    await client.delete_message(message)
    server = ohminator.utils.get_server(message.server)
    if len(server.playlist.yt_playlist) > 0:
        await client.send_message(bot_channel,
                                  f'{message.author.name}: The next song is {server.playlist.yt_playlist[0].title}')
    else:
        await client.send_message(bot_channel, f'{message.author.name}: There is no next song as the queue is empty!')


@RegisterCommand("vote", "v")
async def vote(message, bot_channel, client):
    await client.delete_message(message)
    server = ohminator.utils.get_server(message.server)
    parameters = message.content.split()
    try:
        index = int(parameters[1]) - 1
    except ValueError:
        await client.send_message(bot_channel, f'{message.author.name}: Please give a numeric value!')
        return
    except IndexError:
        await client.send_message(bot_channel, f'{message.author.name}: Please give an index to vote for!')
        return

    try:
        playlist_element = server.playlist.yt_playlist[index]
        if message.author.id in playlist_element.vote_list:
            await client.send_message(bot_channel, f'{message.author.name}: You can only vote once on one entry!')
            return
        playlist_element.vote_list.append(message.author.id)
        for element in server.playlist.yt_playlist:
            if len(element.vote_list) < len(playlist_element.vote_list):
                server.playlist.yt_playlist.remove(playlist_element)
                server.playlist.yt_playlist.insert(server.playlist.yt_playlist.index(element), playlist_element)
                break
        await client.send_message(bot_channel, f'{message.author.name}: {playlist_element.title} has been voted for!')

    except IndexError:
        await client.send_message(bot_channel, f'{message.author.name}: Index {index+1} is out of queue bounds!')


@RegisterCommand("playbuttons")
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


@RegisterCommand("queue", "q", "queuepage")
async def queue_page(message, bot_channel, client):
    await client.delete_message(message)
    server = ohminator.utils.get_server(message.server)
    if len(server.playlist.yt_playlist) == 0:
        await client.send_message(bot_channel, f'{message.author.name}: There is nothing in the queue!')
        return
    parameters = message.content.split()
    try:
        index = int(parameters[1]) - 1
        if not 0 <= index < len(server.playlist.yt_playlist):
            await client.send_message(bot_channel, f'{message.author.name}: Index {index + 1} is out of queue bounds!')
        else:
            await print_from_index(index, server, message, client)
    except ValueError:
        await client.send_message(bot_channel, f'{message.author.name}: Please give a numeric value!')
    except IndexError:
        server.queue_pages = QueuePage(server)
        await server.queue_pages.print_next_page(client)


@RegisterCommand("yttop", "playtop", "pt")
async def play_on_top(message, bot_channel, client):
    server = ohminator.utils.get_server(message.server)
    await play_from_internet(message, bot_channel, client)
    # If the queue is not empty, the last entry must be what was added last.
    # It should not be a race condition as we're not awaiting anything.
    if server.playlist.yt_playlist:
        server.playlist.yt_playlist.insert(0, server.playlist.yt_playlist.pop())


@RegisterCommand("yt", "play", "p")
async def play_from_internet(message, client, db_guild, plugin):
    await message.delete()
    server = ohminator.utils.get_server(message.guild)
    output_channel = message.channel

    if len(message.content.split()) < 2:
        await output_channel.send(f'{message.author.name}: Usage: !yt or !play or !p [link or search term]')
        return

    link_or_phrase = " ".join(message.content.split()[1:])

    # The user must be in a channel to play their link.
    if message.author.voice.channel is None or message.author.voice.afk:
        await output_channel.send(f'{message.author.name}: Please join a voice channel to play your link!')
        return

    # Restricts users to only be able to add songs to playlist if they are in the channel the bot is locked to.
    # This only applies if the player is locked to a channel.
    if server.playlist.summoned_channel:
        if message.author.voice.channel == server.playlist.summoned_channel:
            voice_channel = server.playlist.summoned_channel
        else:
            await output_channel.send_message(f'{message.author.name}: '
                                              f'The bot is locked to channel {server.playlist.summoned_channel.name}. '
                                              'Please join that channel to make Ohminator play audio.')
            return
    else:
        voice_channel = message.author.voice.channel

    # Move if connected with a voice_client. Otherwise, we are not connected to voice and must connect.
    if message.guild.voice_client:
        await message.guild.voice_client.move_to(voice_channel)
    else:
        await voice_channel.connect()

    # Three cases: Case one: An intro is currently playing, so we either append or pause the active player.
    # Case two: Something is already playing, so we queue the requested songs
    # Case three: Nothing is playing, so we just start playing the song
    await server.playlist.playlist_lock.acquire()
    if server.active_tts:
        server.active_tts.stop()
        server.tts_queue.clear()

    async def start_player():
        player = await server.playlist.add_to_playlist(link_or_phrase, False, message.author.name, output_channel)
        server.active_player = await player.get_new_player()
        server.active_playlist_element = player
        server.playlist.now_playing = server.active_player.title
        await output_channel.send(f'{message.author.name}:',
                                  embed=ohminator.utils.create_now_playing_embed(server.active_playlist_element))
        message.guild.voice_client.play(server.active_player, after=server.playlist.after_yt)
    try:
        # Must check if intro is already playing
        if server.intro_player is not None and server.intro_player.is_playing():
            # Check if there's something in the playlist
            if len(server.playlist.yt_playlist) > 0:
                player = await server.playlist.add_to_playlist(link_or_phrase, True, message.author.name, output_channel)
            else:
                await start_player()
                server.active_player.pause()

        elif server.active_player is not None and (
                not server.active_player.is_done() or server.active_player.is_playing()) \
                or len(server.playlist.yt_playlist) > 0:
            player = await server.playlist.add_to_playlist(link_or_phrase, True, message.author.name, output_channel)
        else:
            # Move to the user's voice channel
            if message.guild.voice_client.channel != voice_channel:
                await message.guild.voice_client.move_to(voice_channel)

            await start_player()
    except youtube_dl.utils.UnsupportedError:
        await output_channel.send(f'{message.author.name}: Unsupported URL: That URL is not supported! :slight_frown:')
    except youtube_dl.utils.DownloadError:
        await output_channel.send(f'{message.author.name}: Download Error: '
                                  f'Your link could not be downloaded! :slight_frown:')
    except youtube_dl.utils.MaxDownloadsReached:
        await output_channel.send(f'{message.author.name}: Max downloads reached: '
                                  f'Can not download more videos from YT at the moment. '
                                  'Please wait a moment before trying again. :slight_frown:')
    except youtube_dl.utils.UnavailableVideoError:
        await output_channel.send(f'{message.author.name}: The video is unavailable.')
    except:
        await output_channel.send(f'{message.author.name}: Your link could not be played!')
        traceback.print_exc()
    finally:
        server.playlist.playlist_lock.release()


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
    await client.send_message(message.channel.send(f'{message.author.name}: '
                                                   f'Here is the current queue from index {index+1}:\n{queue.strip()}'))


class QueuePage:
    def __init__(self, server):
        self.page_num = 0
        self.server = server
        self.message = None
        self.end = False

    async def print_next_page(self, client):
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
            self.message = await client.send_message(self.server.bot_channel,
                                                     f'Here is the current queue:\n{queue.strip()}')
        else:
            await client.edit_message(self.message,
                                      f'Here is the current queue:\n{queue.strip()}')


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
                await client.send_message(server.bot_channel,
                                          f'Here is the current queue:\n{queue.strip()}')
            elif message.id == self.volume_up.id:
                if not server.active_player.volume > 1.8:
                    server.active_player.volume += 0.2
            elif message.id == self.volume_down.id:
                if not server.active_player.volume < 0.2:
                    server.active_player.volume -= 0.2
        except:
            traceback.print_exc()


@RegisterCommand("fixaudio")
async def fix_audio(message, bot_channel, client):
    voice_client = client.voice_client_in(message.author.server)
    if voice_client:
        await voice_client.disconnect()
    await client.send_message(bot_channel, f"{message.author.name}: Audio should now be functional again. "
                                           f"If problem persists, please contact the developer or post an issue at "
                                           f"https://github.com/Borgli/Ohminator/issues")
