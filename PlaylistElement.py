import youtube_dl
import functools
import time
import discord.voice_client


class PlaylistElement:
    def __init__(self, link, server, in_client, options, after_yt=None):
        self.link = link
        self.server = server
        self.client = in_client
        self.option = options
        self.after_yt = after_yt
        self.title = str()
        self.description = str()
        self.duration = 0
        self.vote_list = list()
        self.start_time = 0
        self.pause_time = 0
        self.player = None

    def set_yt_info(self, title, duration=None, description=None):
        self.title = title
        self.duration = duration
        self.description = description

    # async def init_player(self):
    #    voice_client = self.client.voice_client_in(self.server)
    #    player = await voice_client.create_ytdl_player(self.link, options=self.option)
    #    self.title = player.title
    #    self.duration = player.duration
    #    return player

    async def get_new_player(self):
        voice_client = self.client.voice_client_in(self.server)
        try:
            player = await voice_client.create_ytdl_player(self.link, options=self.option, after=self.after_yt, ytdl_options={'quiet':True})
        except:
            return None
        self.player = player
        self.title = player.title
        self.duration = player.duration
        self.start_time = time.time()
        player.volume = 0.25
        return player
