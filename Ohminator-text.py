import discord
import discord.channel
import discord.errors
import random
import cleverbot
import re
import os
import urllib
import urllib.request
import signal
from subprocess import check_output
import subprocess
import sys

client = discord.Client()

class Ohminator:
    active_player = None
    intro_player = None
    intro_playing = False
    intro_was_stopped = False
    intro_names = {'runarl', 'Rune', 'Chimeric', 'Johngel', 'Christian Berseth',
                   'Jan Ivar Ugelstad', 'Christian F. Vegard', 'Martin', 'Kristoffer Skau', 'Ginker', 'aekped',
                                                                                                      'sondrehav', "Synspeckter"}
    black_list = {'Christian Berseth', 'Chimeric'}

    test_list = {'Rune', 'Chimeric', 'Christian Berseth', 'Martin'}

    help_message = '{}: List of commands: \n' \
                   '**!help** or **!command**\t\t\t-\tPrints out this menu.\n' \
                   '**!soundhelp**\t\t\t-\tPrints out the sound command menu.\n' \
                   '**!yt** *[youtube link]*\t\t\t-\t  Plays audio from YouTube or other sources in voice channel of caller.\n' \
                   '**!stop**\t\t\t\t\t\t\t\t  -\tStops any playing sound.\n' \
                   '**!joined**\t\t\t\t\t\t\t\t -\tTells you when you joined Ohm!\n' \
                   '**!roll** *[lowest]* *[highest]*\t-\tRoll a number between lowest and highest.\n' \
                   '**!ask** *[sentence]*\t\t\t\t-\t  Use this command to talk to Ohminator.\n' \
                   '**!intro** *[(index)]*\t\t\t\t\t\t\t\t\t-\tPlays one of your intros at random. Can play intro at given index.\n' \
                   '**!introof** *[name of member]* *[(index)]*\t\t\t\t\t\t\t\t\t-\tPlays one intro at random of the given member. Can play intro at given index.\n' \
                   '**!myintros**\t\t\t\t\t\t\t\t\t-\tLists all of your intros.\n' \
                   '**!introlist** or **!listintros** *[name of member]*\t\t\t\t\t\t\t\t\t-\tLists all the intros of the given member.\n' \
                   '**!deleteintro** *[index]*\t\t\t\t\t\t\t\t\t-\tDeletes intro at given index.\n' \
                   '**!upload** *[url]*\t\t\t\-\tUploads a intro. File must be .wav and must be downloaded from Dropbox.\n' \
                   'The url must end on .wav. Example: https://www.dropbox.com/s/znt5tt3xe9vl8su/kekkk.wav. ' \
                   'Ending with ?dl=0 is not acceptable.'

    split_list = list()

    bot_spam = None

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

ohm = Ohminator()
cb = cleverbot.Cleverbot()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print(discord.version_info)
    print(discord.__version__)
    print('------')
    ohm.bot_spam = discord.utils.find(lambda c: c.name == 'bot-spam', client.get_all_channels())

@client.event
async def on_message(message):
    if message.content.startswith('ping'):
        await client.send_message(ohm.bot_spam, 'Pong!')

    elif message.content.startswith('!member'):
        await client.delete_message(message)
        await client.send_message(ohm.bot_spam,
                                  'Not a member yet?'
                                  '\nBecome a member today for a limited time offer of 5$/month.'
                                  '\nEnjoy perks as unlimited YouTube plays, '
                                  'YouTube priority and access to the !spam command!')

    elif message.content.startswith('!spam'):
        await client.delete_message(message)
        await client.send_message(ohm.bot_spam,
                                  '{}: Please pay 5$ to unlock the !spam command.'.format(message.author.name))

    elif message.content.startswith('!ohmage'):
        await client.delete_message(message)
        await client.send_message(ohm.bot_spam, '{}: Ohm was created {}!'.format(message.author.name,
                                                                                    message.server.created_at))

    elif message.content.startswith('fuck'):
        await client.send_message(ohm.bot_spam, 'No, fuck you, {}!'.format(message.author.name))

    elif message.content.startswith('!help') or message.content.startswith('!commands'):
        await client.delete_message(message)
        await client.send_message(ohm.bot_spam, ohm.help_message.format(message.author.name))

    elif message.content.startswith('!ohminator'):
        await client.delete_message(message)
        await client.send_message(ohm.bot_spam, 'I am the Ohminator, bleep, bloop! Type !help to see a list of '
                                                   'commands!')

    elif message.content.startswith('!roll'):
        try:
            options = message.content.split()
            rand = random.randint(int(options[1]), int(options[2]))
            await client.send_message(ohm.bot_spam, '{}: You rolled {}!'.format(message.author.name, rand))
        except:
            await client.send_message(ohm.bot_spam,
                                      '{}: Could not roll with those parameters!'.format(message.author.name))

    elif message.content.startswith('!joined'):
        await client.delete_message(message)
        await client.send_message(ohm.bot_spam, '{}: You joined the Ohm server {}!'.format(message.author.name,
                                                                                              message.author.joined_at))

    elif message.content.startswith('!ask'):
        question = message.content[5:]
        try:
            await client.send_message(ohm.bot_spam, cb.ask(question))
        except Exception as e:
            print(e)
            await client.send_message(ohm.bot_spam, '{}: That is not a question I will answer!'.format(message.author.name))

    elif message.content.startswith('!join'):
        await client.delete_message(message)
        if message.author not in ohm.split_list:
            ohm.split_list.append(message.author)
            await client.send_message(ohm.bot_spam,
                                      '{}: You have joined the queue!\n'
                                      'Current queue: {}'.format(message.author.name, ohm.print_queue()))

    elif message.content.startswith('!leave'):
        await client.delete_message(message)
        ohm.split_list.remove(message.author)
        await client.send_message(ohm.bot_spam,
                                  '{}: You have left the queue!\n'
                                  'Current queue: {}'.format(message.author.name, ohm.print_queue()))

    elif message.content.startswith('!split'):
        await client.delete_message(message)
        try:
            num_teams = int(message.content[7:])
        except:
            await client.send_message(ohm.bot_spam,
                                      '{}: Invalid parameter for !split. Use number of teams!'.format(message.author.name))
            return

        channel_list = list()
        for team_number in range(num_teams):
            channel = discord.utils.get(message.author.server.channels, name='Team {}'.format(team_number + 1))
            if channel is None:
                channel_list.append(
                    await client.create_channel(message.author.server, 'Team {}'.format(team_number + 1),
                                                discord.ChannelType.voice))
            else:
                channel_list.append(channel)

        division = len(ohm.split_list) / float(num_teams)
        random.shuffle(ohm.split_list)
        teams = [ohm.split_list[int(round(division * i)): int(round(division * (i + 1)))] for i in range(num_teams)]

        index = 0
        for team in teams:
            for member in team:
                await client.move_member(member, channel_list[index])
            index += 1

    elif message.content.startswith('!removeteams'):
        await client.delete_message(message)
        team_number = 1
        while True:
            channel = discord.utils.get(message.author.server.channels, name='Team {}'.format(team_number))
            if channel is None:
                break
            else:
                await client.delete_channel(channel)
            team_number += 1

    elif message.content.startswith('!myintros'):
        await client.delete_message(message)
        intro_list = os.listdir('{}/intros'.format(message.author.name))
        intro_print = str()
        index_cnt = 1
        for intro in intro_list:
            intro_print += '\n**[{}]**:\t{}'.format(index_cnt, intro)
            index_cnt += 1
        await client.send_message(ohm.bot_spam,
                                  '{}: Intro list:{}'.format(message.author.mention, intro_print))

    elif message.content.startswith('!deleteintro'):
        await client.delete_message(message)
        try:
            intro_index = int(message.content[12:])
            if intro_index < 1 or intro_index > 5:
                await client.send_message(ohm.bot_spam,
                                          '{}: Index is out of bounds!'.format(message.author.name))
                return
        except:
            await client.send_message(ohm.bot_spam,
                                      '{}: Invalid parameter. Must be the index of the intro to delete!'.format(message.author.name))
            return

        try:
            intro_list = os.listdir('{}/intros'.format(message.author.name))
            await client.send_message(ohm.bot_spam,
                                      '{}: Deleting intro {} at index {}'.format(
                                          message.author.name, intro_list[intro_index-1], intro_index-1))
            os.remove('{}/intros/{}'.format(message.author.name, intro_list[intro_index-1]))
        except:
            await client.send_message(ohm.bot_spam,
                                      '{}: Could not remove file. No file found at given index.'.format(message.author.name))
            return

    elif message.content.startswith('!upload'):
        await client.delete_message(message)
        url = message.content[8:]
        try:
            find_name = re.findall(r'\/([a-zA-z\d]+?.wav).*?$', url)
            file_name = find_name.pop()
        except:
            await client.send_message(ohm.bot_spam,'{}: Invalid file.'.format(message.author.name))
            return
        intro_list = os.listdir('{}/intros'.format(message.author.name))
        if (len(intro_list)+1) > 5:
            await client.send_message(ohm.bot_spam,
                                      '{}: You have reached the maximum number of intros. '
                                      'Please delete an intro before uploading a new one'.format(
                                          message.author.name))
            return
        url += '?dl=1&pv=1'

        file, header = urllib.request.urlretrieve(url)
        path = os.path.realpath(file)
        os.rename(path, '{}/intros/{}'.format(message.author.name, file_name))
        await client.send_message(ohm.bot_spam, '{}: Upload successful.'.format(message.author.name))

    elif message.content.startswith('!restart'):
        await client.delete_message(message)
        pid_list = map(int, check_output(["pidof", "python3.5"]).split())
        my_pid = os.getpid()
        for pid in pid_list:
            if pid != my_pid:
                os.kill(pid, signal.SIGKILL)
        subprocess.Popen(["python3.5", "Ohminator-sound.py"] + sys.argv[1:])

client.run('MTc2NDMzMTMwMzM1NTAyMzM3.CgvoFg.FLaupAZZ5OviZ1Fb7gAO_Aq-sLo')

