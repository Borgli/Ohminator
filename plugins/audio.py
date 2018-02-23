import math
import os
import random
import time
import traceback
from tempfile import mkstemp

import youtube_dl
from gtts import gTTS
from utils import register_command, get_server

import utils
import discord
import asyncio


@register_command("tts", "say")
async def text_to_speech(message, bot_channel, client):
    await client.delete_message(message)
    text = message.content[5:]
    server = utils.get_server(message.server)
    if not server.next_tts_created:
        client.loop.create_task(play_next_tts(server, client))
        server.next_tts_created = True
    await server.playlist.playlist_lock.acquire()
    if message.author.voice_channel is None or message.author.voice.is_afk:
        await client.send_message(bot_channel,
                                  '{}: Please join a voice channel to use text-to-speech!'.format(
                                      message.author.name))
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
                                      '{}: Language setting is not a valid setting! Please fix.'.format(message.author.name))
            return

        # Handles playing intros when the bot is summoned
        if server.playlist.summoned_channel:
            if message.author.voice.voice_channel == server.playlist.summoned_channel:
                voice_channel = server.playlist.summoned_channel
            else:
                await client.send_message(bot_channel,
                                          '{}: The bot is locked to channel {}. '
                                          'Please join that channel to use !tts.'.format(
                                              message.author.name, server.playlist.summoned_channel.name))
                return
        else:
            voice_channel = message.author.voice_channel

        voice_client = await utils.connect_to_voice(client, message.author.server, voice_channel)
        # voice_client = client.voice_client_in(message.author.server)
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
            await client.send_message(bot_channel,
                                      '{}: Could not connect to voice channel!'.format(message.author.name))
            return
        '''

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
    if voice_channel:
        channel = voice_channel
    else:
        channel = message.author.voice_channel
    voice_client = client.voice_client_in(message.author.server)
    if voice_client:
        await voice_client.disconnect()
    voice_client = await client.join_voice_channel(voice_channel)
    '''
    try:
        if voice_client is None:
            voice_client = await client.join_voice_channel(channel)
        elif voice_client.channel is None:
            await voice_client.disconnect()
            voice_client = await client.join_voice_channel(channel)
        elif voice_client.channel != channel:
            await voice_client.move_to(channel)
    except:
        await client.send_message(bot_channel,
                                  '{}: Could not connect to voice channel!'.format(message.author.name))
        traceback.print_exc()
        return
    '''


@register_command("summon", "lock", "acquire")
async def summon(message, bot_channel, client):
    await client.delete_message(message)
    parameters = message.content.split()
    server = utils.get_server(message.server)
    # If there's a parameter it should be the channel you want the bot locked to
    if len(parameters) > 1:
        try:
            channel = server.get_channel(parameters[1])
            if channel.type == discord.ChannelType.voice:
                server.playlist.summoned_channel = channel.discord_channel
                await connect_to_voice_channel(message, bot_channel, client, voice_channel=channel.discord_channel)
                await client.send_message(bot_channel, "{}: Locked to channel {}".format(message.author.name,
                                                                                         channel.name))
            else:
                await client.send_message(bot_channel, "{}: That channel is a text channel, not a voice channel.\n"
                                                       "Usage: !summon [(channel id or name)]".format(message.author.name))
        except utils.NoChannelFoundError:
            await client.send_message(bot_channel, "{}: Couldn't find a channel matching the parameter!\n"
                                                   "Usage: !summon [(channel id or name)]".format(message.author.name))
    else:
        if message.author.voice.voice_channel:
            server.playlist.summoned_channel = message.author.voice.voice_channel
            await connect_to_voice_channel(message, bot_channel, client)
            await client.send_message(bot_channel, "{}: Locked to channel {}"
                                      .format(message.author.name, message.author.voice.voice_channel.name))
        else:
            await client.send_message(bot_channel, "{}: You must be in a voice channel "
                                                   "to use this command without a channel id.\n"
                                                   "Usage: !summon [(channel id)]".format(message.author.name))


@register_command("unsummon", "desummon", "release")
async def unsummon(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    await client.send_message(bot_channel, "{}: Released from channel {}"
                              .format(message.author.name, server.playlist.summoned_channel.name))
    server.playlist.summoned_channel = None


@register_command("volume", "sv")
async def volume(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    if server.active_player is None or server.active_player.is_done():
        await client.send_message(bot_channel, '{}: Nothing is playing!'.format(message.author.name))
    else:
        parameters = message.content.split()
        if len(parameters) < 2:
            current_volume = server.active_player.volume
        else:
            try:
                current_volume = float(parameters[1])/2/100.0
            except ValueError:
                await client.send_message(bot_channel, '{}: Please give a numeric value!'.format(message.author.name))
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
            await client.send_message(bot_channel, '{}: {}, the volume for the current track is {}%!'.format(
                icon, message.author.name, int(current_volume*2*100.0)))
        elif parameters[1] == current_volume:
            await client.send_message(bot_channel, '{}: {}, the volume is already the given value!'.format(
                icon, message.author.name))
        else:
            if current_volume < 0.0:
                current_volume = 0.0
            elif current_volume > 0.5:
                current_volume = 0.5

            await client.send_message(bot_channel, '{}: {}, the volume was changed from {}% to {}%!'.format(
                icon, message.author.name, int(server.active_player.volume*2*100.0), int(current_volume*2*100.0)))
            server.active_player.volume = current_volume


@register_command("stop", "s", "stahp", "stap")
async def stop(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    if server.active_player is None or not server.active_player.is_playing():
        await client.send_message(bot_channel, '{}: No active player to stop!'.format(message.author.name))
    else:
        await client.send_message(bot_channel,
                                  ':stop_button:: {} stopped the player and cleared the queue!'.format(message.author.name))
        server.playlist.yt_playlist.clear()
        server.active_player.stop()


@register_command("pause", "pa")
async def pause(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    if server.active_player is None:
        await client.send_message(bot_channel, '{}: Nothing to pause!'.format(message.author.name))
    elif not server.active_player.is_playing():
        await client.send_message(bot_channel, '{}: The player is not playing because it was stopped'
                                               ' or is already paused!'.format(message.author.name))
    else:
        await client.send_message(bot_channel, ':pause_button:: {} paused the player!'.format(message.author.name))
        server.active_playlist_element.pause_time = time.time()
        server.active_player.pause()


@register_command("resume", "r")
async def resume(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    if server.active_player is None or server.active_player.is_done():
        await client.send_message(bot_channel, '{}: Nothing to resume!'.format(message.author.name))
    else:
        await client.send_message(bot_channel, ':arrow_forward:: {} resumed the player!'.format(message.author.name))
        server.active_playlist_element.start_time += (server.active_playlist_element.pause_time-server.active_playlist_element.start_time)
        server.active_player.resume()


@register_command("repeat", "again", "a")
async def repeat(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    if server.active_player is None or not server.active_player.is_playing():
        await client.send_message(bot_channel, '{}: Nothing to repeat!'.format(message.author.name))
    else:
        await client.send_message(bot_channel,
                                  ':repeat: {} repeated {}.'.format(message.author.name,
                                                                              server.active_playlist_element.title))
        server.playlist.yt_playlist.insert(0, server.active_playlist_element)


@register_command("shuffle", "sh")
async def shuffle(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    if server.active_player is None or not server.active_player.is_playing():
        await client.send_message(bot_channel, '{}: Nothing to shuffle!'.format(message.author.name))
    else:
        await client.send_message(bot_channel,
                                  ':twisted_rightwards_arrows: {} shuffled the list.'.format(message.author.name))
        random.shuffle(server.playlist.yt_playlist)
        server.playlist.yt_playlist.sort(key=lambda element: len(element.vote_list), reverse=True)


@register_command("delete", "d", "remove")
async def delete(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    parameters = message.content.split()
    try:
        index = int(parameters[1]) - 1
    except ValueError:
        await client.send_message(bot_channel, '{}: Please give a numeric value!'.format(message.author.name))
        return
    except IndexError:
        await client.send_message(bot_channel, '{}: Please give an index to delete!'.format(message.author.name))
        return

    try:
        playlist_element = server.playlist.yt_playlist[index]
        server.playlist.yt_playlist.remove(playlist_element)
        await client.send_message(bot_channel, "{}: Entry '{}' with index {} was deleted from the queue.".format(message.author.name, playlist_element.title, index+1))
    except IndexError:
        await client.send_message(bot_channel, '{}: Index {} is out of queue bounds!'.format(message.author.name, index+1))


@register_command("skip", "sk")
async def skip(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    await server.playlist.playlist_lock.acquire()
    try:
        if server.active_player is None and len(server.playlist.yt_playlist) > 0:
            await client.send_message(bot_channel, '{}: Nothing to skip!'.format(message.author.name))
        else:
            await client.send_message(bot_channel, ':track_next:: {} skipped the song!'.format(message.author.name))
            server.active_player.stop()
    finally:
        server.playlist.playlist_lock.release()


@register_command("next", "n")
async def next(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    if len(server.playlist.yt_playlist) > 0:
        await client.send_message(bot_channel,
                                  '{}: The next song is {}'.format(message.author.name, server.playlist.yt_playlist[
                                      0].title))
    else:
        await client.send_message(bot_channel,
                                  '{}: There is no next song as the queue is empty!'.format(message.author.name))

# Unused. Should be refactored! Has been replaced by queue_page function.
async def q(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    if len(server.playlist.yt_playlist) > 0:
        cnt = 1
        queue = str()
        more_entries = False
        for play in server.playlist.yt_playlist:
            if cnt <= 30:
                votes = ''
                if len(play.vote_list) > 0:
                    votes = ' **[{}]**'.format(len(play.vote_list))
                queue += "{}: {}{}\n".format(cnt, play.title, votes)
            else:
                more_entries = True
            cnt += 1
        if more_entries is True:
            if cnt-30 == 1:
                entry = 'entry'
            else:
                entry = 'entries'
            queue += "And {} {} more...".format(cnt-30, entry)
        await client.send_message(bot_channel,
                                  '{}: Here is the current queue:\n{}'.format(message.author.name, queue.strip()))
    else:
        await client.send_message(bot_channel, '{}: There is nothing in the queue!'.format(message.author.name))


@register_command("vote", "v")
async def vote(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    parameters = message.content.split()
    try:
        index = int(parameters[1]) - 1
    except ValueError:
        await client.send_message(bot_channel, '{}: Please give a numeric value!'.format(message.author.name))
        return
    except IndexError:
        await client.send_message(bot_channel, '{}: Please give an index to vote for!'.format(message.author.name))
        return

    try:
        playlist_element = server.playlist.yt_playlist[index]
        if message.author.id in playlist_element.vote_list:
            await client.send_message(bot_channel,
                                      '{}: You can only vote once on one entry!'.format(message.author.name))
            return
        playlist_element.vote_list.append(message.author.id)
        for element in server.playlist.yt_playlist:
            if len(element.vote_list) < len(playlist_element.vote_list):
                server.playlist.yt_playlist.remove(playlist_element)
                server.playlist.yt_playlist.insert(server.playlist.yt_playlist.index(element), playlist_element)
                break
        await client.send_message(bot_channel,
                                  '{}: {} has been voted for!'.format(message.author.name, playlist_element.title))

    except IndexError:
        await client.send_message(bot_channel, '{}: Index {} is out of queue bounds!'.format(message.author.name, index+1))


@register_command("playbuttons")
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


@register_command("queue", "q", "queuepage")
async def queue_page(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    if len(server.playlist.yt_playlist) == 0:
        await client.send_message(bot_channel,
                                  '{}: There is nothing in the queue!'.format(message.author.name))
        return
    parameters = message.content.split()
    try:
        index = int(parameters[1]) - 1
        if not 0 <= index < len(server.playlist.yt_playlist):
            await client.send_message(bot_channel,
                                      '{}: Index {} is out of queue bounds!'.format(message.author.name, index + 1))
        else:
            await print_from_index(index, server, message, client)
    except ValueError:
        await client.send_message(bot_channel, '{}: Please give a numeric value!'.format(message.author.name))
    except IndexError:
        server.queue_pages = QueuePage(server)
        await server.queue_pages.print_next_page(client)


@register_command("yttop", "playtop", "pt")
async def play_on_top(message, bot_channel, client):
    server = utils.get_server(message.server)
    await play_from_internet(message, bot_channel, client)
    # If the queue is not empty, the last entry must be what was added last.
    # It should not be a race condition as we're not awaiting anything.
    if server.playlist.yt_playlist:
        server.playlist.yt_playlist.insert(0, server.playlist.yt_playlist.pop())


@register_command("yt", "play", "p")
async def play_from_internet(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)

    if len(message.content.split()) < 2:
        await client.send_message(bot_channel,
                                  '{}: Usage: !yt or !play or !p [link or search term]'.format(
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

    voice_client = await utils.connect_to_voice(client, message.author.server, voice_channel)
    # Check if the voice client is okay to use. If not, it is changed.
    # The voice client is retrieved later when the playlist starts a new song.
    # voice_client = client.voice_client_in(message.author.server)
    '''
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
    '''

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


async def print_from_index(index, server, message, client):
    play = server.playlist.yt_playlist
    queue = str()
    try:
        for i in range(index, index + 30, 1):
            votes = ''
            if len(play[i].vote_list) > 0:
                votes = ' **[{}]**'.format(len(play[i].vote_list))
            queue += "{}: {}{}\n".format(i + 1, play[i].title, votes)
        queue += "Total entries: {}\n".format(len(play))
    except IndexError:
        queue += "End of queue!"
    await client.send_message(server.bot_channel,
                              '{}: Here is the current queue from index {}:\n{}'.format(message.author.name,
                                                                                        index+1, queue.strip()))


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
                    votes = ' **[{}]**'.format(len(play[i].vote_list))
                queue += "{}: {}{}\n".format(i+1, play[i].title, votes)

            pages_left = math.ceil((len(play)-((self.page_num*30)+29))/30)
            queue += "Total entries: {}\n".format(len(play))
            if pages_left > 0:
                queue += "There {} {} {} left".format(pages_left == 1 and 'is' or 'are', pages_left, pages_left == 1 and 'page' or 'pages')
        except IndexError:
            queue += "End of queue!"
            self.end = True

        self.page_num += 1
        if self.message is None:
            self.message = await client.send_message(self.server.bot_channel,
                                      'Here is the current queue:\n{}'.format(queue.strip()))
        else:
            await client.edit_message(self.message,
                                          'Here is the current queue:\n{}'.format(queue.strip()))


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
                        queue += "{}: {}\n".format(cnt, play.title)
                    else:
                        more_entries = True
                    cnt += 1
                if more_entries is True:
                    if cnt - 30 == 1:
                        entry = 'entry'
                    else:
                        entry = 'entries'
                    queue += "And {} {} more...".format(cnt - 30, entry)
                await client.send_message(server.bot_channel,
                                          'Here is the current queue:\n{}'.format(queue.strip()))
            elif message.id == self.volume_up.id:
                if not server.active_player.volume > 1.8:
                    server.active_player.volume += 0.2
            elif message.id == self.volume_down.id:
                if not server.active_player.volume < 0.2:
                    server.active_player.volume -= 0.2
        except:
            traceback.print_exc()


@register_command("fixaudio")
async def fix_audio(message, bot_channel, client):
    voice_client = client.voice_client_in(message.author.server)
    if voice_client:
        await voice_client.disconnect()
    await client.send_message(bot_channel, "{}: Audio should now be functional again. If problem persists,"
                                           "please contact the developer or post an issue at "
                                           "https://github.com/Borgli/Ohminator/issues".format(message.author.name))
