import asyncio
import discord
import discord.errors
import pickle
import re
from PlaylistElement import PlaylistElement
from os.path import exists
from os import remove
import Server
import youtube_dl
import functools
import logging
import traceback
import time
import math


class Playlist:
    def __init__(self, client, server):
        self.client = client
        self.server = server
        self.yt_playlist = list()
        self.queue_exists = None
        self.pinned_message_bot_spam = None
        self.pinned_message_ohm = None
        self.now_playing = str()
        # Fetch pinned messages from persistent memory
        # if exists('servers/{}/pinned_message_bot_spam.pickle'.format(server.server_loc)):
        #    with open('servers/{}/pinned_message_bot_spam.pickle'.format(server.server_loc)) as f:
        #        self.pinned_message_bot_spam = pickle.load(f);
        self.play_next = asyncio.Event()
        self.clear_now_playing = asyncio.Event()
        self.after_yt_lock = asyncio.Lock()
        self.add_to_playlist_lock = asyncio.Lock()

        logging.basicConfig(filename='logs/ohminator.log', level=logging.ERROR)
        client.loop.create_task(self.manage_pinned_messages())
        client.loop.create_task(self.play_next_yt())
        client.loop.create_task(self.should_clear_now_playing())

    async def manage_pinned_messages(self):
        await self.client.wait_until_ready()
        await asyncio.sleep(1, loop=self.client.loop)
        while not self.client.is_closed:
            # Constructing the queue string
            cnt = 1
            queue = str()
            for play in self.yt_playlist:
                if cnt > 10:
                    break
                votes = ''
                if len(play.vote_list) > 0:
                    votes = ' **[{}]**'.format(len(play.vote_list))
                queue += "**{}**: {}{}\n".format(cnt, play.title, votes)
                cnt += 1

            try:
                # Check if a pinned message exists
                if self.pinned_message_bot_spam is None:
                    # Check if a pinned message pickle file exists
                    if exists('servers/{}/pinned_message_bot_spam.pickle'.format(self.server.server_loc)):
                        # Open the file to read
                        with open('servers/{}/pinned_message_bot_spam.pickle'.format(self.server.server_loc),
                                  'r+b') as f:
                            self.pinned_message_bot_spam = pickle.load(f)

                    else:
                        # If it doesn't exist we must create a new one
                        self.pinned_message_bot_spam = await self.client.send_message(self.server.bot_channel,
                                                                                      'Setting up pinned message...')
                        # Write the new message to file
                        with open('servers/{}/pinned_message_bot_spam.pickle'.format(self.server.server_loc),
                                  'w+b') as f:
                            pickle.dump(self.pinned_message_bot_spam, f)

                    # Remove previously pinned messages
                    pinned_messages = await self.client.pins_from(self.server.bot_channel)
                    for message in pinned_messages:
                        if message.id != self.pinned_message_bot_spam.id:
                            await self.client.delete_message(message)

                    # Pin the message
                    await self.client.pin_message(self.pinned_message_bot_spam)

                player = self.server.active_playlist_element
                # Edit the content of the message with the current playlist info
                if self.server.active_player is not None and not self.server.active_player.is_playing() \
                        and not self.server.active_player.is_done():
                    await self.client.edit_message(self.pinned_message_bot_spam, ':pause_button: '
                                                                                 '**Paused:** {}\n'
                                                                                 '**Current queue:**\n{}\n'.format(
                                                                                    self.now_playing, queue.strip()))
                else:
                    if player is None or self.server.active_player.is_done():
                        await self.client.edit_message(self.pinned_message_bot_spam, '**Now playing:** {}\n'
                                                                                     '**Current queue:**\n{}\n'.format(
                            self.now_playing, queue.strip()))
                    else:
                        current_time = int((time.time()-player.start_time))
                        end_time = player.duration
                        progress_step = int(math.ceil((((current_time/end_time)*100)/10)))
                        white_space = "<" + ('='*(10-progress_step))
                        progress_bar = "" + ('='*progress_step) + ">" + white_space + ""
                        m, s = divmod(current_time, 60)
                        h, m = divmod(m, 60)
                        current_time = "{}:{}:{}".format(h, m, s) if h != 0 else "{}:{}".format(m, s if s>9 else "0"+ str(s))
                        m, s = divmod(end_time, 60)
                        h, m = divmod(m, 60)
                        end_time = "{}:{}:{}".format(h, m, s) if h != 0 else "{}:{}".format(m, s if s>9 else "0"+ str(s))
                        await self.client.edit_message(self.pinned_message_bot_spam, '`[{}][{}][{}]`\n**Now playing:** {}\n'
                                                                                     '**Current queue:**\n{}\n'.format(
                                                                                        current_time, progress_bar, end_time, self.now_playing, queue.strip()))
            except (ValueError, AttributeError) as f:
                remove('servers/{}/pinned_message_bot_spam.pickle'.format(self.server.server_loc))
                self.pinned_message_bot_spam = None
                traceback.print_exc()
            except discord.errors.Forbidden as f:
                print("Missing privilege post to channel {} on server {}".format(self.pinned_message_bot_spam.channel,
                                                                                 self.server.name))
            except discord.errors.HTTPException as f:
                if f.response.status == 400:
                    remove('servers/{}/pinned_message_bot_spam.pickle'.format(self.server.server_loc))
                    self.pinned_message_bot_spam = None
                    traceback.print_exc()
                elif f.response.status == 500:
                    # INTERNAL SERVER ERROR
                    print("Internal server error on server {}".format(self.server.name))
                    await asyncio.sleep(30, loop=self.client.loop)
                else:
                    traceback.print_exc()
            except:
                logging.error('Manage pinned messages on server {} had an exception:\n'.format(self.server.name),
                              exc_info=True)
                traceback.print_exc()
                await asyncio.sleep(60, loop=self.client.loop)

            # Bot spam will always have pinned messages, but this enables it to work on other channels as well.
            # This should be refactored in the near future
            for channel in self.server.channel_list:
                try:
                    # Check if channel as pinned messages enabled
                    if channel.type != discord.ChannelType.text or \
                                    channel.list_settings()['pin_yt_playlists'] != "True" or \
                                    channel.id == self.server.bot_channel.id:
                        continue
                    # Check if a pinned message pickle file exists
                    pickle_loc = 'servers/{}/channels/{}/pinned_message.pickle'.format(self.server.server_loc,
                                                                                       channel.channel_loc)
                    if exists(pickle_loc):
                        # Open the file to read
                        with open(pickle_loc, 'r+b') as f:
                            pinned_message = pickle.load(f)

                    else:
                        # If it doesn't exist we must create a new one
                        pinned_message = await self.client.send_message(self.server.discord_server.get_channel(channel.id),
                                                                        'Setting up pinned message...')
                        # Write the new message to file
                        with open(pickle_loc, 'w+b') as f:
                            pickle.dump(pinned_message, f)

                    # Remove previously pinned messages
                    pinned_messages = await self.client.pins_from(self.server.discord_server.get_channel(channel.id))
                    for message in pinned_messages:
                        if message.id != pinned_message.id:
                            await self.client.delete_message(message)

                    # Pin the message
                    await self.client.pin_message(pinned_message)

                    # Edit the content of the message with the current playlist info
                    if self.server.active_player is not None and not self.server.active_player.is_playing() \
                            and not self.server.active_player.is_done():
                        await self.client.edit_message(pinned_message, ':pause_button: **Paused:** {}\n'
                                                                        '**Current queue:**\n{}\n'.format(
                                                                        self.now_playing, queue.strip()))
                    else:
                        await self.client.edit_message(pinned_message, '**Now playing:** {}\n'
                                                                        '**Current queue:**\n{}\n'.format(
                                                                            self.now_playing, queue.strip()))
                except (ValueError, AttributeError) as f:
                    remove(pickle_loc)
                    traceback.print_exc()
                except discord.errors.HTTPException as f:
                    if f.response.status == 400:
                        if pickle_loc is not None:
                            remove(pickle_loc)
                        else:
                            traceback.print_exc()
                    elif f.response.status == 500:
                        # INTERNAL SERVER ERROR
                        print("Internal server errror on server {}".format(self.server.name))
                        await asyncio.sleep(30, loop=self.client.loop)
                    else:
                        traceback.print_exc()
                except:
                    logging.error('Manage pinned messages on server {} had an exception:\n'.format(self.server.name),
                                  exc_info=True)
                    traceback.print_exc()
                    await asyncio.sleep(60, loop=self.client.loop)
            # 3 second intervals
            await asyncio.sleep(0.5, loop=self.client.loop)

    def get_options(self, link):
        try:
            outstring = re.findall(r'\?t=(.*)', link)
            timestamps = re.findall(r'(\d+)', outstring.pop())

            to_convert = [0, 0, 0]
            stamp_i = len(timestamps) - 1
            for index in range(len(to_convert)):
                if stamp_i >= 0:
                    to_convert[index] = timestamps[stamp_i]
                    stamp_i -= 1
                else:
                    break

            seconds = int(to_convert[0])

            if seconds > 59:
                m, s = divmod(seconds, 60)
                h, m = divmod(m, 60)
                option = '-ss {}:{}:{}'.format(h, m, s)
            else:
                option = '-ss {}:{}:{}'.format(to_convert[2], to_convert[1], to_convert[0])
            print(option)
            return option
        except:
            return None

    async def add_to_playlist(self, link, append, name):
        option = self.get_options(link)
        opts = {
            'format': 'webm[abr>0]/bestaudio/best',
            'quiet': True,
            'logger': MyLogger()
        }
        if option is not None and isinstance(option, dict):
            opts.update(option)

        ydl = youtube_dl.YoutubeDL(opts)

        try:
            # Case number 1: The link is any URL
            func = functools.partial(ydl.extract_info, link, download=False, process=False)
            info = await self.client.loop.run_in_executor(None, func)
        except youtube_dl.DownloadError as e:
            # Case number 2: The link is a search link
            if not re.fullmatch(r'https?://(www.youtube.com|youtu.be)/\S+', link):
                link = 'ytsearch:{}'.format(link)
                try:
                    # Process = True to recieve titles
                    func = functools.partial(ydl.extract_info, link, download=False, process=True)
                    info = await self.client.loop.run_in_executor(None, func)
                except:
                    raise
            else:
                # Case number 3: The link is broken
                try:
                    await self.client.send_message(self.server.bot_channel,
                                                   '{}: Sorry! {}'.format(name, e.exc_info[1].args[0]))
                except IndexError:
                    pass
                raise

        playlist_element = None
        if "entries" in info:
            entries = list(info.get("entries"))
            if len(entries) > 1:
                # PLAYLIST
                playlist_element = self.add_to_queue(option, entries, append)
                await self.client.send_message(self.server.bot_channel,
                                                    '{}: The playlist {} has been added to the queue.'
                                                    ''.format(name, info["title"]))
            else:
                entry = entries[0]
                playlist_element = PlaylistElement(link, self.server, self.client, option, self.after_yt)
                playlist_element.set_yt_info(entry["title"])
                if append:
                    self.yt_playlist.append(playlist_element)
                    await self.client.send_message(self.server.bot_channel,
                                                    '{}: {} has been added to the queue.'.format(name, entry["title"]))
        else:
            # NORMAL
            playlist_element = PlaylistElement(link, self.server, self.client, option, self.after_yt)
            playlist_element.set_yt_info(info.get('title'))
            if append:
                self.yt_playlist.append(playlist_element)
                await self.client.send_message(self.server.bot_channel,
                                               '{}: {} has been added to the queue.'.format(name, info.get("title")))
        return playlist_element

    def add_to_queue(self, option, entries, append):
        entry = entries.pop(0)
        playlist_element = PlaylistElement(entry["url"], self.server, self.client, option, self.after_yt)
        playlist_element.set_yt_info(entry["title"])
        if append and not (playlist_element.title == '[Deleted video]' or playlist_element.title == '[Private video]'):
            self.yt_playlist.append(playlist_element)

        for entry in entries:
            p_e = PlaylistElement(entry["url"], self.server, self.client, option, self.after_yt)
            title = entry.get('title')
            if title == '[Deleted video]' or title == '[Private video]':
                continue
            p_e.set_yt_info(title)
            self.yt_playlist.append(p_e)

        return playlist_element

    def after_yt(self):
        # print('{} finished. After-yt starting.'.format(self.server.active_player.title))
        self.client.loop.call_soon_threadsafe(self.clear_now_playing.set)
        self.client.loop.call_soon_threadsafe(self.play_next.set)
        # print("YouTube-video finished playing.")

    async def play_next_yt(self):
        while not self.client.is_closed:
            await self.play_next.wait()
            # print("{} will now play next yt.".format(self.server.name))
            await self.add_to_playlist_lock.acquire()
            if len(self.yt_playlist) > 0:
                something_to_play = False
                while True:
                    if len(self.yt_playlist) <= 0:
                        self.play_next.clear()
                        self.add_to_playlist_lock.release()
                        break
                    player = self.yt_playlist.pop(0)
                    self.server.active_player = await player.get_new_player()
                    self.server.active_playlist_element = player
                    if self.server.active_player is not None:
                        something_to_play = True
                        break
                if something_to_play:
                    self.now_playing = self.server.active_player.title
                    await self.client.send_message(self.server.bot_channel,
                                                   'Now playing: {}\nIt is {} seconds long'.format(
                                                       self.server.active_player.title,
                                                       self.server.active_player.duration))
                    self.server.active_player.start()
            self.play_next.clear()
            self.add_to_playlist_lock.release()

    async def should_clear_now_playing(self):
        while not self.client.is_closed:
            await self.clear_now_playing.wait()
            self.now_playing = ""
            self.clear_now_playing.clear()


# The sole purpose of this class is to suppress output from youtube-dl
class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass
