
class Settings:
    def get_settings(self):
        return dict(self.__dict__.items())


class ServerSettings(Settings):

    def __init__(self):
        self.tts_language = "no"


class ClientSettings(Settings):

    def __init__(self):
        self.pin_yt_playlists = "False"
