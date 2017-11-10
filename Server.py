import pickle

from Member import Member
from os.path import isdir
from os import mkdir, listdir
from os.path import exists
import asyncio
from Playlist import Playlist
from IntroManager import IntroManager
import discord
from Channel import Channel
from settings import ServerSettings
import datetime
from utils import *

class Server:
    def __init__(self, discord_server: discord.Server, client: discord.Client, db):
        # Initialize everything that is not persistent
        self.name = discord_server.name
        self.id = discord_server.id
        self.server_loc = '{}_{}'.format(discord_server.name, discord_server.id)
        self.default_channel = discord_server.default_channel
        self.discord_server = discord_server
        self.db = db
        self.client = client

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
        self.prefix = '!'

        self.wow_lock = asyncio.Lock()

        # added for polling
        self.poll_time = 30

        # Handle server document
        self.server_doc = db.Servers.find_one({"_id": discord_server.id})
        if self.server_doc is None:
            self.server_doc = {
                "_id": discord_server.id,
            }
            db.Servers.insert_one(self.server_doc)

        # Handle server settings
        self.settings = ServerSettings()
        if 'settings' in self.server_doc:
            self.change_settings(self.server_doc['settings'])
        else:
            self.change_settings(dict())

        # Create members folder if it doesn't exist
        if not exists('servers/{}/members'.format(self.server_loc)):
            mkdir('servers/{}/members'.format(self.server_loc))

        # Initialize members
        for member in discord_server.members:
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

        # Create default intros folder if it doesn't exist
        if not exists('servers/{}/default_intros'.format(self.server_loc)):
            mkdir('servers/{}/default_intros'.format(self.server_loc))

        self.playlist = Playlist(client, self)
        self.intro_manager = IntroManager(client, self)
        client.loop.create_task(self.check_for_birthdays())

    def change_settings(self, in_settings):
        for setting, value in in_settings.items():
            setattr(self.settings, setting, value)
        self.server_doc['settings'] = self.list_settings()
        self.db.Servers.update_one({'_id': self.discord_server.id}, {'$set' : {'settings': self.server_doc['settings']}})

    def list_settings(self):
        return self.settings.get_settings()

    def get_member(self, id):
        for member in self.member_list:
            if (id == member.id) and (self.id == member.server.id):
                return member
        raise NoMemberFoundError

    def get_channel(self, id):
        for channel in self.channel_list:
            if id == channel.id or id == channel.name:
                return channel
        raise NoChannelFoundError

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

    async def check_for_birthdays(self):
        await self.client.wait_until_ready()
        await asyncio.sleep(1, loop=self.client.loop)
        while not self.client.is_closed:
            todays_date = datetime.date.today()
            todays_day_and_month = "{}.{}".format(todays_date.day, todays_date.month)
            for member in self.member_list:
                if not 'birthday' in member.birthday:
                    continue
                birthday = member.birthday['birthday']
                day_and_month = "{}.{}".format(birthday.day, birthday.month)
                if day_and_month == todays_day_and_month and (not 'congratulated' in member.birthday or
                                                                             member.birthday['congratulated'] != todays_date):
                    await self.client.send_message(self.bot_channel, "Happy Birthday, **{}**!".format(member.mention))
                    member.birthday['congratulated'] = todays_date
                    # Save birthday to pickle
                    birthday_pickle = 'servers/{}/members/{}/birthday.pickle'.format(self.server_loc,
                                                                                     member.member_loc)
                    with open(birthday_pickle, 'w+b') as f:
                        pickle.dump(member.birthday, f)
            await asyncio.sleep(10, loop=self.client.loop)
