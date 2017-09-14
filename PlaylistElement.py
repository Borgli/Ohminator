import time


class PlaylistElement:
    def __init__(self, link, server, in_client, options, after_yt=None, entry=None):
        self.link = link
        self.server = server
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
                                                           before_options="-reconnect_streamed 1"
                                                                          " -reconnect_delay_max 5",
                                                           after=self.after_yt, ytdl_options={'quiet':True})
        except:
            return None
        self.player = player
        self.title = player.title
        self.duration = player.duration
        self.start_time = time.time()
        player.volume = 0.25
        return player

    def __repr__(self):
        return self.title
