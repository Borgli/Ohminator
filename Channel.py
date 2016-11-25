from os.path import exists

class Channel:

    def __init__(self, client, server, channel):
        self.name = channel.name
        self.id = channel.id
        self.channel_loc = '{}-{}'.format(channel.name, channel.id)

        settings_pickle = 'servers/{}/channels/{}/settings.pickle'.format(server.server_loc, self.channel_loc)
        if exists(settings_pickle):
            # Initialize everything persistent
            with open(settings_pickle, 'r+b') as f:
                pass
