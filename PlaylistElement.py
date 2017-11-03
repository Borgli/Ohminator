import os
import time

import functools
import traceback

import youtube_dl


class PlaylistElement:
    def __init__(self, link, server, in_client, options, ytdl, after_yt=None, entry=None):
        self.link = link
        self.server = server
        self.client = in_client
        self.option = options
        self.ytdl = ytdl
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
        self.downloaded_file = None
        if entry:
            self.title = entry.get("title")
            self.duration = entry.get("duration")
            self.description = entry.get("description")
            self.thumbnail = entry.get("thumbnail")
            if not self.thumbnail:
                self.thumbnail = "https://i.ytimg.com/vi/{}/mqdefault.jpg".format(entry.get("url"))
            self.webpage_url = entry.get("webpage_url")
            if not self.webpage_url:
                self.webpage_url = "https://www.youtube.com/watch?v={}".format(entry.get("url"))

    async def get_new_player(self):
        voice_client = self.client.voice_client_in(self.server)
        try:
            player = await voice_client.create_ytdl_player(self.webpage_url, options=self.option,
                                                           after=self.after_yt, ytdl_options={'quiet': True})
        except:
            return None
        self.player = player
        self.title = player.title
        self.duration = player.duration
        self.start_time = time.time()
        player.volume = 0.25
        return player

    async def get_next_player(self):
        voice_client = self.client.voice_client_in(self.server)
        filename = 'servers/{}/{}.mp3'.format(self.server.server_loc, self.title)
        try:
            if not os.path.exists(filename):
                raise FileNotFoundError("File {} does not exist when it should!".format(filename))
            player = voice_client.create_ffmpeg_player(filename, options=self.option, after=self.after_yt)
        except:
            traceback.print_exc()
            return None
        self.player = player
        setattr(self.player, 'title', self.title)
        self.start_time = time.time()
        player.volume = 0.25
        return player

    async def download_next_song(self):
        # First, check if element is next in queue
        if self.server.playlist.yt_playlist[0] != self:
            return

        filename = 'servers/{}/{}.{}'.format(self.server.server_loc, self.title, '{}')
        # Second, check if currently playing song is the same as this one.
        # This is to prevent downloading same song twice.
        if os.path.exists(filename.format('mp3')):
            return

        # Third, download song
        opts = {
            'format': 'webm[abr>0]/bestaudio/best',
            'quiet': True,
            'logger': self.server.playlist.MyLogger(),
            'outtmpl': filename.format('%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }

        if self.option is not None and isinstance(self.option, dict):
            opts.update(self.option)

        ydl = youtube_dl.YoutubeDL(opts)
        func = functools.partial(ydl.extract_info, self.webpage_url)
        await self.client.loop.run_in_executor(None, func)

    def __repr__(self):
        return self.title
