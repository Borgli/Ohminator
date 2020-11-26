import asyncio
import discord
import discord.errors
import pickle
import re
from os.path import exists
from os import remove, mkdir

from discord.player import AudioPlayer

import youtube_dl
import functools
import logging
import traceback
import time
import math
from datetime import datetime

from firebase_admin import db
from utils import create_now_playing_embed, update_active_player


class Playlist:
    def __init__(self, client, guild):
        self.client = client
        self.guild = guild
        #self.yt_playlist = list()
        self.queue_exists = None
        self.pinned_message_bot_spam = None
        self.pinned_message_ohm = None
        self.now_playing = str()
        self.play_next = asyncio.Event()
        self.clear_now_playing = asyncio.Event()
        self.after_yt_lock = asyncio.Lock()
        self.playlist_lock = asyncio.Lock()
        self.summoned_channel = None
        self.active_audio_source = None

        if not exists("logs"):
            mkdir("logs")
        logging.basicConfig(filename='logs/ohminator.log', level=logging.ERROR)

    @staticmethod
    def get_options(link):
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
                option = f'-ss {h}:{m}:{s}'
            else:
                option = f'-ss {to_convert[2]}:{to_convert[1]}:{ to_convert[0]}'
            print(option)
            return option
        except:
            return None

    @staticmethod
    def extract_info(entry, link):
        title = entry.get("title")
        duration = entry.get("duration")
        if duration:
            duration = int(duration)
        description = entry.get("description")

        def is_yt_link():
            return link.startswith("ytsearch") or link.startswith("https://www.youtube.com/")
        thumbnail = entry.get("thumbnail")
        if not thumbnail and is_yt_link():
            thumbnail = f"https://i.ytimg.com/vi/{entry.get('url')}/mqdefault.jpg"
        webpage_url = entry.get("webpage_url")
        if not webpage_url and is_yt_link():
            webpage_url = f"https://www.youtube.com/watch?v={entry.get('url')}"
        elif not webpage_url:
            webpage_url = link
        return {"title": title, "duration": duration, "description": description,
                "thumbnail": thumbnail, "webpage_url": webpage_url}

    async def add_to_playlist(self, link, append, name, output_channel, user=None):
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
            # Might cause problems as self.client.loop has been unreliable before.
            # Might be worth spawning a new process.
            info = await self.client.loop.run_in_executor(None, func)
        except youtube_dl.DownloadError as e:
            # Case number 2: The link is a search link
            if not re.fullmatch(r'https?://(www.youtube.com|youtu.be)/\S+', link):
                link = f'ytsearch:{link}'
                try:
                    # Process = True to receive titles
                    func = functools.partial(ydl.extract_info, link, download=False, process=True)
                    info = await self.client.loop.run_in_executor(None, func)
                except:
                    raise
            else:
                # Case number 3: The link is broken
                try:
                    await output_channel.send(f'{name}: Sorry! {e.exc_info[1].args[0]}')
                except IndexError:
                    pass
                raise

        active_player_ref = db.reference(f"guilds/{self.guild.id}/active_player")
        active_player = active_player_ref.get()
        if not active_player:
            active_player = {}
        active_player["queue"] = active_player.get("queue", [])
        if "entries" in info:
            entries = list(info.get("entries"))
            if len(entries) > 1:
                # PLAYLIST
                link = self.add_to_queue(option, entries, append, user)
                await output_channel.send(f'{name}: The playlist {info["title"]} has been added to the queue.')
            else:
                entry = entries[0]
                info = self.extract_info(entry, link)
                if append:
                    active_player["queue"].append({
                        "title": info["title"], "link": info["webpage_url"], "duration": info["duration"],
                        "thumbnail": info["thumbnail"], "user": user
                    })
                    active_player_ref.update({"queue": active_player["queue"]})
                    await output_channel.send(f'{name}: {info["title"]} has been added to the queue.')
        else:
            # NORMAL
            info = self.extract_info(info, link)
            if append:
                active_player["queue"].append({
                    "title": info["title"], "link": info["webpage_url"], "duration": info["duration"],
                    "thumbnail": info["thumbnail"], "user": user
                })
                active_player_ref.update({"queue": active_player["queue"]})
                await output_channel.send(f'{name}: {info["title"]} has been added to the queue.')
        return await YTDLSource.from_url(link, stream=True, start=option)

    def add_to_queue(self, option, entries, append, user):
        entry = entries.pop(0)
        active_player_ref = db.reference(f"guilds/{self.guild.id}/active_player")
        active_player = active_player_ref.get()
        active_player["queue"] = active_player.get("queue", [])
        if append and not (entry.get("title") == '[Deleted video]' or entry.get("title") == '[Private video]'):
            info = self.extract_info(entry, entry["url"])
            active_player["queue"].append({
                "title": info["title"], "link": info["webpage_url"], "duration": info["duration"],
                "thumbnail": info["thumbnail"], "user": user
            })

        for entry in entries:
            title = entry.get('title')
            if title == '[Deleted video]' or title == '[Private video]':
                continue
            info = self.extract_info(entry, entry["url"])
            active_player["queue"].append({
                "title": info["title"], "link": info["webpage_url"], "duration": info["duration"],
                "thumbnail": info["thumbnail"], "user": user
            })

        active_player_ref.update({"queue": active_player["queue"]})
        return entry["url"]

    def after_yt(self, error):
        if error:
            print(error)
            traceback.print_exc()

        queue = db.reference(f"guilds/{self.guild.id}/active_player/queue").get()
        output_channel = self.guild.get_channel(db.reference(f"guilds/{self.guild.id}/bot_channel").get())
        if queue:
            next_song = queue.pop()
            fut = asyncio.run_coroutine_threadsafe(YTDLSource.from_url(next_song["link"], stream=True), self.client.loop)
            try:
                audio_source = fut.result()
                coro = output_channel.send(f'{next_song["user"]}:',
                                           embed=create_now_playing_embed(
                                               update_active_player(audio_source,
                                                                    db.reference(f"guilds/{self.guild.id}"),
                                                                    next_song["user"]))
                                           )
                fut = asyncio.run_coroutine_threadsafe(coro, self.client.loop)
                fut.result()
                self.active_audio_source = audio_source
                self.guild.voice_client.play(audio_source, after=self.after_yt)
            except:
                traceback.print_exc()
            db.reference(f"guilds/{self.guild.id}/active_player/").update({
                "queue": queue
            })
        else:
            db.reference(f"guilds/{self.guild.id}/active_player").delete()
            self.active_audio_source = None


# The sole purpose of this class is to suppress output from youtube-dl
class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn -loglevel quiet',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


# TODO: Use ytdl / info object from outside.
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.25):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, start=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        if start:
            ffmpeg_options['before_options'] += " " + start
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class PlaylistElement:
    def __init__(self, link, guild, in_client, options, after_yt=None, entry=None):
        self.link = link
        self.guild = guild
        self.client = in_client
        self.option = options
        self.after_yt = after_yt
        self.title = str()
        self.description = str()
        self.thumbnail = str()
        self.webpage_url = str()
        self.duration = 0
        self.vote_list = list()
        self.start_time = 0
        self.pause_time = 0
        self.player = None
        self.audio_source = None
        if entry:
            self.title = entry.get("title")
            self.duration = entry.get("duration")
            if self.duration:
                self.duration = int(self.duration)
            self.description = entry.get("description")

            def is_yt_link():
                return link.startswith("ytsearch") or link.startswith("https://www.youtube.com/")
            self.thumbnail = entry.get("thumbnail")
            if not self.thumbnail and is_yt_link():
                self.thumbnail = f"https://i.ytimg.com/vi/{entry.get('url')}/mqdefault.jpg"
            self.webpage_url = entry.get("webpage_url")
            if not self.webpage_url and is_yt_link():
                self.webpage_url = f"https://www.youtube.com/watch?v={entry.get('url')}"
            elif not self.webpage_url:
                self.webpage_url = link

    async def get_new_audio_source(self):
        audio_source = await YTDLSource.from_url(self.webpage_url, stream=True)
        #player = AudioPlayer(audio_source, self.guild.voice_client, after=self.after_yt)
        #self.player = player
        self.title = audio_source.title
        # TODO: Fix this hack!
        #player.title = audio_source.title
        #player.is_done = lambda: player._end.is_set()
        #self.duration = player.duration
        #if self.duration:
        #    self.duration = int(self.duration)
        #self.start_time = time.time()
        self.audio_source = audio_source
        return audio_source

    def __repr__(self):
        return self.title
