
class Settings:
    def get_settings(self):
        return dict(self.__dict__.items())

    def update_settings(self, collection, query):
        doc = collection.find_one(query)
        if doc:
            for setting, value in doc['settings'].items():
                setattr(self, setting, value)

class ServerSettings(Settings):

    def __init__(self):
        self.tts_language = "no"


class ClientSettings(Settings):

    def __init__(self):
        self.pin_yt_playlists = "False"
