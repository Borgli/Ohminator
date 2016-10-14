
class PlaylistElement:
    link = ""
    server = None
    option = ""
    title = ""
    duration = None

    def __init__(self, link, server, in_client, options, after_yt):
        self.link = link
        self.server = server
        self.client = in_client
        self.option = options
        self.after_yt = after_yt

    async def init_player(self):
        voice_client = self.client.voice_client_in(self.server)
        player = await voice_client.create_ytdl_player(self.link, options=self.option)
        self.title = player.title
        self.duration = player.duration
        return player

    async def get_new_player(self):
        voice_client = self.client.voice_client_in(self.server)
        player = await voice_client.create_ytdl_player(self.link, options=self.option, after=self.after_yt)
        return player
