import time
import traceback


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
            if self.duration:
                self.duration = int(self.duration)
            self.description = entry.get("description")

            def is_yt_link():
                return link.startswith("ytsearch") or link.startswith("https://www.youtube.com/")
            self.thumbnail = entry.get("thumbnail")
            if not self.thumbnail and is_yt_link():
                self.thumbnail = "https://i.ytimg.com/vi/{}/mqdefault.jpg".format(entry.get("url"))
            self.webpage_url = entry.get("webpage_url")
            if not self.webpage_url and is_yt_link():
                self.webpage_url = "https://www.youtube.com/watch?v={}".format(entry.get("url"))
            elif not self.webpage_url:
                self.webpage_url = link

    async def get_new_player(self):
        voice_client = self.client.voice_client_in(self.server)
        player = await voice_client.create_ytdl_player(self.webpage_url, options=self.option,
                                                       after=self.after_yt, ytdl_options={'quiet':True})
        self.player = player
        self.title = player.title
        self.duration = player.duration
        if self.duration:
            self.duration = int(self.duration)
        self.start_time = time.time()
        player.volume = 0.25
        return player

    def __repr__(self):
        return self.title
