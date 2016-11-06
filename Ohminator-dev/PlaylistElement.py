import youtube_dl
import functools

class PlaylistElement:
    link = ""
    server = None
    option = ""
    title = ""
    duration = None
    entries = None
    description = None

    def __init__(self, link, server, in_client, options, after_yt=None):
        self.link = link
        self.server = server
        self.client = in_client
        self.option = options
        self.after_yt = after_yt

    def set_yt_info(self, title, duration=None, description=None):
        self.title = title
        self.duration = duration
        self.description = description

    #async def init_player(self):
    #    voice_client = self.client.voice_client_in(self.server)
    #    player = await voice_client.create_ytdl_player(self.link, options=self.option)
    #    self.title = player.title
    #    self.duration = player.duration
    #    return player

    async def get_new_player(self):
        voice_client = self.client.voice_client_in(self.server)
        player = await voice_client.create_ytdl_player(self.link, options=self.option, after=self.after_yt)
        self.title = player.title
        self.duration = player.duration
        player.volume = 0.25
        return player
