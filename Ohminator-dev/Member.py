from Stats import Stats
from os.path import exists
from os import mkdir, listdir


class Member:
    def __init__(self, client, server, member):
        self.stats = Stats()
        self.name = member.name
        self.id = member.id
        self.member_loc = '{}-{}'.format(member.name, member.id)
        self.server = server

        self.intro_folder = 'servers/{}/members/{}/intros'.format(server.server_loc, self.member_loc)
        # Create intros folder if it doesn't exist
        if not exists(self.intro_folder):
            mkdir(self.intro_folder)

        member_pickle = 'servers/{}/members/{}/member.pickle'.format(server.server_loc, self.member_loc)
        if exists(member_pickle):
            # Initialize everything persistent
            with open(member_pickle, 'r+b') as f:
                pass

    def has_intro(self):
        # Check if the member has intros
        self.intro_list = listdir(self.intro_folder)
        if len(self.intro_list) > 0:
            return True
        else:
            return False