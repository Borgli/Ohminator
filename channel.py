import pickle
from os.path import exists, join

from settings import ClientSettings


class Channel:
    def __init__(self, client, server, channel):
        self.name = channel.name
        self.id = channel.id
        self.channel_loc = '{}-{}'.format(channel.name, channel.id)
        self.type = channel.type
        self.discord_channel = channel

        self.settings_pickle = join(join(join(join(join('servers', server.server_loc), 'channels',
                                                   self.channel_loc, 'settings.pickle'))))
        if exists(self.settings_pickle):
            # Load settings
            with open(self.settings_pickle, 'r+b') as f:
                self.settings = pickle.load(f)
        else:
            self.settings = ClientSettings()
            with open(self.settings_pickle, 'w+b') as f:
                pickle.dump(self.settings, f)

    def change_settings(self, in_settings):
        for setting, value in in_settings.items():
            setattr(self.settings, setting, value)
            with open(self.settings_pickle, 'w+b') as f:
                pickle.dump(self.settings, f)

    def list_settings(self):
        return self.settings.__dict__
