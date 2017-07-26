from Member import Member
from os.path import isdir
from os import mkdir
from os.path import exists
import pickle
from discord.utils import find
import asyncio
from Playlist import Playlist
from IntroManager import IntroManager
import discord
from Channel import Channel
from settings import ServerSettings

class Server:
    def __init__(self, discord_server: discord.Server, client: discord.Client):
        # Initialize everything that is not persistent
        self.name = discord_server.name
        self.id = discord_server.id
        self.server_loc = '{}_{}'.format(discord_server.name, discord_server.id)
        self.default_channel = discord_server.default_channel
        self.discord_server = discord_server

        self.member_list = list()
        self.channel_list = list()
        self.bot_channel = None
        self.default_channel = None
        self.playlist = None
        self.intro_manager = None
        self.active_player = None
        self.active_playlist_element = None
        self.intro_player = None
        self.split_list = list()
        self.playbuttons = None
        self.queue_pages = None
        self.tts_queue = list()
        self.next_tts = asyncio.Event()
        self.next_tts_created = False
        self.active_tts = None

        #playbuttons_message = 'servers/{}/playbuttons.pickle'.format(self.server_loc)
        #if (exists('servers/{}/playbuttons.pickle'.format(self.server_loc))):
        #    with open(playbuttons_message, 'w+b') as f:
        #        self.playbuttons = pickle.load(f)

        server_pickle = 'servers/{}/server.pickle'.format(self.server_loc)
        if exists(server_pickle):
            # Initialize everything persistent
            with open(server_pickle, 'r+b') as f:
                pass

        # Handle server settings
        self.settings_pickle = 'servers/{}/settings.pickle'.format(self.server_loc)
        if exists(self.settings_pickle):
            # Load settings
            with open(self.settings_pickle, 'r+b') as f:
                self.settings = pickle.load(f)
        else:
            self.settings = ServerSettings()
            with open(self.settings_pickle, 'w+b') as f:
                pickle.dump(self.settings, f)

        # Create members folder if it doesn't exist
        if not exists('servers/{}/members'.format(self.server_loc)):
            mkdir('servers/{}/members'.format(self.server_loc))

        # Initialize members
        for member in discord_server.members:
            member_loc = '{}-{}'.format(member.name, member.id)
            if not isdir('servers/{}/members/{}'.format(self.server_loc, member_loc)):
                mkdir('servers/{}/members/{}'.format(self.server_loc, member_loc))
            self.member_list.append(Member(client, self, member))

        # Create channels folder if it doesn't exist
        if not exists('servers/{}/channels'.format(self.server_loc)):
            mkdir('servers/{}/channels'.format(self.server_loc))

        # Initialize channels
        for channel in discord_server.channels:
            channel_loc = '{}-{}'.format(channel.name, channel.id)
            if not isdir('servers/{}/channels/{}'.format(self.server_loc, channel_loc)):
                mkdir('servers/{}/channels/{}'.format(self.server_loc, channel_loc))
            self.channel_list.append(Channel(client, self, channel))

        self.playlist = Playlist(client, self)
        self.intro_manager = IntroManager(client, self)

    def change_settings(self, in_settings):
        for setting, value in in_settings.items():
            setattr(self.settings, setting, value)
            with open(self.settings_pickle, 'w+b') as f:
                pickle.dump(self.settings, f)

    def list_settings(self):
        return self.settings.__dict__

    def get_member(self, id):
        for member in self.member_list:
            if (id == member.id) and (self.id == member.server.id):
                return member

    def get_channel(self, id):
        for channel in self.channel_list:
            if id == channel.id or id == channel.name:
                return channel

    def print_queue(self):
        print_line = str()
        first = True
        for entry in self.split_list:
            if first:
                print_line += '{}'.format(entry.name)
                first = False
            else:
                print_line += ', {}'.format(entry.name)
        return print_line


#async def save_to_file():
#    await client.wait_until_ready()
#    await asyncio.sleep(10, loop=client.loop)
#    while not client.is_closed:
#        for server in Events.server_list:
#            with open('servers/{}/server.pickle'.format(server.server_loc), 'w+b') as f:
#                pickle.dump(server, f)
#        await asyncio.sleep(5, loop=client.loop)

#client.loop.create_task(save_to_file())
