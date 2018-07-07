import pickle

from stats import Stats
from os.path import exists, isdir, join
from os import mkdir, listdir
from utils import create_if_not_exists


class Member:
    def __init__(self, client, server, member):
        self.stats = Stats()
        self.name = member.name
        self.id = member.id
        self.mention = member.mention
        self.member_loc = '{}'.format(member.id)
        self.server = server
        self.birthday = dict()

        # This is for the poll function
        self.question = None
        self.options = list()

        server_dir = join('servers', server.server_loc)
        member_dir = join(join(server_dir, 'members'), self.member_loc)
        create_if_not_exists(member_dir)

        self.intro_folder = join(member_dir, 'intros')
        # Create intros folder if it doesn't exist
        create_if_not_exists(self.intro_folder)

        birthday_pickle = join(member_dir, 'birthday.pickle')
        if exists(birthday_pickle):
            # Get birthday from pickle
            with open(birthday_pickle, 'r+b') as f:
                self.birthday = pickle.load(f)

        member_pickle = join(member_dir, 'member.pickle')
        if exists(member_pickle):
            # Initialize everything persistent
            with open(member_pickle, 'r+b') as f:
                pass

    def has_intro(self):
        # Check if the member has intros
        intro_list = listdir(self.intro_folder)
        if len(intro_list) > 0:
            return True
        else:
            return False
