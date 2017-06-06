
class Settings:
    pass


class ServerSettings(Settings):

    def __init__(self):
        self.tts_language = "no"


class ClientSettings(Settings):

    def __init__(self):
        self.pin_yt_playlists = "False"
