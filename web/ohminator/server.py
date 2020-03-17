import pickle

from ohminator.member import Member
from os.path import isdir
from os import mkdir, listdir
from os.path import exists
from os.path import join
import asyncio
from ohminator.playlist import Playlist
import discord
from ohminator.channel import Channel
from ohminator.settings import ServerSettings
import datetime
from ohminator.utils import *
from ohminator.plugins.intro import IntroManager


class Guild(discord.guild.Guild):
    def __init__(self, discord_guild):
        self.id = discord_guild.id
        self.name = discord_guild.name


class Server:
    def __init__(self, guild: discord.Guild, client: discord.Client, db):
        # Initialize everything that is not persistent
        self.name = guild.name
        self.id = guild.id
        self.server_loc = str(guild.id)
        self.guild = guild
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

        create_if_not_exists(join('servers', self.server_loc))

        server_dir = join('servers', self.server_loc)
        # Create members folder if it doesn't exist
        create_if_not_exists(join(server_dir, 'members'))

        # Initialize members
        for member in guild.members:
            self.member_list.append(Member(client, self, member))

        # Create channels folder if it doesn't exist
        create_if_not_exists(join(server_dir, 'channels'))

        # Initialize channels
        for channel in guild.channels:
            self.channel_list.append(Channel(client, self, channel))

        # Create default intros folder if it doesn't exist
        create_if_not_exists(join(server_dir, 'default_intros'))

        self.playlist = Playlist(client, self, guild)
        self.intro_manager = IntroManager(client, self)
        client.loop.create_task(self.check_for_birthdays())

    def change_settings(self, in_settings):
        for setting, value in in_settings.items():
            setattr(self.settings, setting, value)
        self.server_doc['settings'] = self.list_settings()
        self.db.Servers.update_one({'_id': self.discord_server.id}, {'$set': {'settings': self.server_doc['settings']}})

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
        if len(self.split_list) == 0:
            return 'The queue is empty!'
        print_line = str()
        first = True
        for entry in self.split_list:
            if first:
                print_line += str(entry.name)
                first = False
            else:
                print_line += f', {entry.name}'
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
