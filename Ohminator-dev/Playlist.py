import asyncio
import discord
import discord.errors
import pickle
import re
from PlaylistElement import PlaylistElement
from os.path import exists
import Server


class Playlist:
    yt_playlist = list()

    play_next = asyncio.Event()
    clear_now_playing = asyncio.Event()
    after_yt_lock = asyncio.Lock()

    queue_exists = None
    pinned_message_bot_spam = None
    pinned_message_ohm = None
    now_playing = ""

    def __init__(self, client, server):
        self.client = client
        self.server = server
        # Fetch pinned messages from persistent memory
        # if exists('servers/{}/pinned_message_bot_spam.pickle'.format(server.server_loc)):
        #    with open('servers/{}/pinned_message_bot_spam.pickle'.format(server.server_loc)) as f:
        #        self.pinned_message_bot_spam = pickle.load(f);

        client.loop.create_task(self.manage_pinned_messages())
        client.loop.create_task(self.play_next_yt())
        client.loop.create_task(self.should_clear_now_playing())

    async def manage_pinned_messages(self):
        await self.client.wait_until_ready()
        await asyncio.sleep(10, loop=self.client.loop)
        while not self.client.is_closed:
            cnt = 1
            queue = str()
            for play in self.yt_playlist:
                queue += "{}: {}\n".format(cnt, play.title)
                cnt += 1

            if self.pinned_message_bot_spam is None:
                if exists('servers/{}/pinned_message_bot_spam.pickle'.format(self.server.server_loc)):
                    with open('servers/{}/pinned_message_bot_spam.pickle'.format(self.server.server_loc), 'r+b') as f:
                        self.pinned_message_bot_spam = pickle.load(f)
                else:
                    self.pinned_message_bot_spam = await self.client.send_message(self.server.bot_channel,
                                                                                  '**Now playing:** {}\n**Current queue:**\n{}\n'.format(
                                                                                         self.now_playing, queue.strip()))
                try:
                    await self.client.pin_message(self.pinned_message_bot_spam)
                except discord.errors.HTTPException:
                    self.pinned_message_bot_spam = await self.client.send_message(self.server.bot_channel,
                                                                                  '**Now playing:** {}\n**Current queue:**\n{}\n'.format(
                                                                                      self.now_playing, queue.strip()))
            else:
                await self.client.edit_message(self.pinned_message_bot_spam,
                                               '**Now playing:** {}\n**Current queue:**\n{}\n'.format(self.now_playing,
                                                                                                      queue.strip()))
                with open('servers/{}/pinned_message_bot_spam.pickle'.format(self.server.server_loc), 'w+b') as f:
                    pickle.dump(self.pinned_message_bot_spam, f)
            await asyncio.sleep(5, loop=self.client.loop)

    def add_to_playlist(self, link):
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
        except:
            option = None

        playlist_element = PlaylistElement(link, self.server, self.client, option, self.after_yt)
        return playlist_element

    def after_yt(self):
        self.client.loop.call_soon_threadsafe(self.clear_now_playing.set)
        self.client.loop.call_soon_threadsafe(self.play_next.set)
        print("YouTube-video finished playing.")

    async def play_next_yt(self):
        while not self.client.is_closed:
            await self.play_next.wait()
            if len(self.yt_playlist) > 0:
                self.server.active_player = await self.yt_playlist.pop(0).get_new_player()
                #await self.client.change_presence(game=discord.Game(name=self.server.active_player.title))
                self.now_playing = self.server.active_player.title
                await self.client.send_message(self.server.bot_channel,
                                               'Now playing: {}\nIt is {} seconds long'.format(
                                                   self.server.active_player.title,
                                                   self.server.active_player.duration))
                self.server.active_player.start()
            self.play_next.clear()

    async def should_clear_now_playing(self):
        while not self.client.is_closed:
            await self.clear_now_playing.wait()
            #await self.client.change_presence(game=discord.Game())
            self.now_playing = ""
            self.clear_now_playing.clear()
