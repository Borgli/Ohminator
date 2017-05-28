import time
import traceback

from gtts import gTTS
import utils
import math
import discord
from tempfile import TemporaryFile, mkstemp
import os

async def text_to_speech(message, bot_channel, client):
    await client.delete_message(message)
    text = message.content[5:]
    server = utils.get_server(message.server)
    if not server.next_tts_created:
        client.loop.create_task(play_next_tts(server, client))
        server.next_tts_created = True
    await server.playlist.add_to_playlist_lock.acquire()
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

        tts = gTTS(text=text, lang='no')
        voice_client = client.voice_client_in(message.server)
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

        fd, filename = mkstemp()

        def after_tts():
            client.loop.call_soon_threadsafe(server.next_tts.set)
            os.remove(filename)

        tts.save(filename)
        server.active_tts = voice_client.create_ffmpeg_player(filename, after=after_tts)
        server.active_tts.start()
    finally:
        server.playlist.add_to_playlist_lock.release()

async def play_next_tts(server, client):
    while not client.is_closed:
        await server.next_tts.wait()
        await server.playlist.add_to_playlist_lock.acquire()
        if (server.intro_player is not None and server.intro_player.is_playing()) or (server.active_player is not None
            and (not server.active_player.is_done() or server.active_player.is_playing())):
            server.tts_queue.clear()
        else:
            if len(server.tts_queue) > 0:
                something_to_play = False
                while True:
                    if len(server.tts_queue) <= 0:
                        server.next_tts.clear()
                        server.playlist.add_to_playlist_lock.release()
                        break
                    text = server.tts_queue.pop(0)
                    tts = gTTS(text=text, lang='no')

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
        server.next_tts.clear()
        server.playlist.add_to_playlist_lock.release()


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
                current_volume = float(parameters[1])/100.0
            except ValueError:
                await client.send_message(bot_channel, '{}: Please give a numeric value!'.format(message.author.name))
                return

        if current_volume <= 0.0:
            icon = ':mute:'
        elif 0.0 < current_volume < 0.67:
            icon = ':speaker:'
        elif 0.66 < current_volume < 1.33:
            icon = ':sound:'
        else:
            icon = ':loud_sound:'

        if len(parameters) < 2:
            await client.send_message(bot_channel, '{}: {}, the volume for the current track is {}%!'.format(icon, message.author.name, int(current_volume*100.0)))
        elif parameters[1] == current_volume:
            await client.send_message(bot_channel, '{}: {}, the volume is already the given value!'.format(icon, message.author.name))
        else:
            if current_volume < 0.0:
                current_volume = 0.0
            elif current_volume > 0.5:
                current_volume = 0.5
            await client.send_message(bot_channel, '{}: {}, the volume was changed from {}% to {}%!'.format(icon, message.author.name, int(server.active_player.volume*100.0), int(current_volume*100.0)))
            server.active_player.volume = current_volume

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

async def resume(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    if server.active_player is None or server.active_player.is_done():
        await client.send_message(bot_channel, '{}: Nothing to resume!'.format(message.author.name))
    else:
        await client.send_message(bot_channel, ':arrow_forward:: {} resumed the player!'.format(message.author.name))
        server.active_playlist_element.start_time += (server.active_playlist_element.pause_time-server.active_playlist_element.start_time)
        server.active_player.resume()


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

async def skip(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    if server.active_player is None or not server.active_player.is_playing():
        await client.send_message(bot_channel, '{}: Nothing to skip!'.format(message.author.name))
    else:
        await client.send_message(bot_channel, ':track_next:: {} skipped the song!'.format(message.author.name))
        server.active_player.stop()

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
        await client.send_message(bot_channel, '{}: Please give an index to delete!'.format(message.author.name))
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
                                             '{}: Here is the current queue from index {}:\n{}'.format(message.author.name, index+1, queue.strip()))


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
