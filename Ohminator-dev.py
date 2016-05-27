import discord
import discord.channel
import asyncio
import random
import cleverbot
import time
import re

client = discord.Client()

class Ohminator:
    active_player = None
    intro_names = {'runarl', 'Rune', 'Chimeric', 'Johngel',
                   'Jan Ivar Ugelstad', 'Christian F. Vegard', 'Martin', 'Kristoffer Skau', 'Ginker', 'aekped',
                                                                                                      'sondrehav'}
    black_list = {'Christian Berseth', 'Chimeric'}

    help_message = '{}: List of commands: \n' \
                   '**!help** or **!command**\t\t\t-\tPrints out this menu.\n' \
                   '**!yt** *[youtube link]*\t\t\t-\t  Plays audio from YouTube in voice channel of caller.\n' \
                   '**!stahp**\t\t\t\t\t\t\t\t  -\tStops any playing sound.\n' \
                   '**!joined**\t\t\t\t\t\t\t\t -\tTells you when you joined Ohm!\n' \
                   '**!roll** *[lowest]* *[highest]*\t-\tRoll a number between lowest and highest.\n' \
                   '**!intro**\t\t\t\t\t\t\t\t\t-\tPlays your intro.\n' \
                   '**!ask** *[sentence]*\t\t\t\t-\t  Use this command to talk to Ohminator.\n'

    split_list = list()

    def print_queue(self):
        print_line = str()
        first = True
        for entry in self.split_list:
            if first:
                print_line += '{}'.format(entry.name)
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

@client.event
async def on_message(message):
    if message.content.startswith('ping'):
        await client.send_message(message.channel, 'Pong!')

    elif message.content.startswith('!yt'):
        link = message.content[4:]
        await client.delete_message(message)

        if message.author.voice_channel is None or message.author.is_afk:
            await client.send_message(message.channel,
                                      '{}: Please join a voice channel to play your link!'.format(message.author.name))
            return

        if ohm.active_player is not None and ohm.active_player.is_playing():
            await client.send_message(message.channel,
                                      '{}: Something is already playing!'.format(message.author.name))
            return

        voice_client = client.voice_client_in(message.author.server)
        try:
            if voice_client is None:
                voice_client = await client.join_voice_channel(message.author.voice_channel)
            elif voice_client.channel != message.author.voice_channel:
                await voice_client.move_to(message.author.voice_channel)
        except:
            await client.send_message(message.channel,
                                      '{}: Could not connect to voice channel!'.format(message.author.name))
            return

        try:
            outstring = re.findall(r'\?t=(.*)', message.content)
            timestamps = re.findall(r'(\d+)', outstring.pop())

            to_convert = [0, 0, 0]
            stamp_i = len(timestamps) - 1
            for index in range(len(to_convert)):
                if stamp_i >= 0:
                    to_convert[index] = timestamps[stamp_i]
                    stamp_i -= 1
                else:
                    break

            option = '-ss {}:{}:{}'.format(to_convert[2], to_convert[1], to_convert[0])
            print(option)
        except:
            option = None

        try:
            ohm.active_player = await voice_client.create_ytdl_player(link, options=option)
            await client.send_message(message.channel,
                                      '{}: \nNow playing: {}\nIt is {} seconds long'.format(message.author.name,
                                                                                            ohm.active_player.title,
                                                                                            ohm.active_player.duration))
            ohm.active_player.start()
        except:
            await client.send_message(message.channel, '{}: Your link could not be played!'.format(message.author.name))

    elif message.content.startswith('!stahp') or message.content.startswith('!stop'):
        await client.delete_message(message)
        if ohm.active_player is None or not ohm.active_player.is_playing:
            await client.send_message(message.channel, '{}: No active player!'.format(message.author.name))
        else:
            await client.send_message(message.channel, '{} stopped the player!'.format(message.author.name))
            ohm.active_player.stop()

    elif message.content.startswith('!intro'):
        await client.delete_message(message)
        if message.author.voice_channel is None or message.author.is_afk:
            return

        if message.author.name is not None and message.author.name in ohm.intro_names:

            voice_client = client.voice_client_in(message.author.server)
            try:
                if voice_client is None:
                    voice_client = await client.join_voice_channel(message.author.voice_channel)
                elif voice_client.channel != message.author.voice_channel:
                    await voice_client.move_to(message.author.voice_channel)
            except Exception as e:
                print(e)
                await client.send_message(message.channel,
                                          '{}: Could not connect to voice channel!'.format(message.author.name))
                return

            if ohm.active_player is not None and ohm.active_player.is_playing():
                ohm.active_player.stop()

            try:
                ohm.active_player = voice_client.create_ffmpeg_player('{}/intro.wav'.format(message.author.name))
                ohm.active_player.start()
            except Exception as e:
                print(e)
                await client.send_message(message.channel,
                                          '{}: Could not play intro!'.format(message.author.name))
            return

    elif message.content.startswith('!member'):
        await client.delete_message(message)
        await client.send_message(message.channel,
                                  'Not a member yet?'
                                  '\nBecome a member today for a limited time offer of 5$/month.'
                                  '\nEnjoy perks as unlimited YouTube plays, '
                                  'YouTube priority and access to the !spam command!')

    elif message.content.startswith('!spam'):
        await client.delete_message(message)
        await client.send_message(message.channel,
                                  '{}: Please pay 5$ to unlock the !spam command.'.format(message.author.name))

    elif message.content.startswith('!ohmage'):
        await client.delete_message(message)
        await client.send_message(message.channel, '{}: Ohm was created {}!'.format(message.author.name,
                                                                                    message.server.created_at))

    elif message.content.startswith('fuck'):
        await client.send_message(message.channel, 'No, fuck you, {}!'.format(message.author.name))

    elif message.content.startswith('!help') or message.content.startswith('!commands'):
        await client.delete_message(message)
        await client.send_message(message.channel, ohm.help_message.format(message.author.name))

    elif message.content.startswith('!ohminator'):
        await client.delete_message(message)
        await client.send_message(message.channel, 'I am the Ohminator, bleep, bloop! Type !help to see a list of '
                                                   'commands!')

    elif message.content.startswith('!roll'):
        try:
            options = message.content.split()
            rand = random.randint(int(options[1]), int(options[2]))
            await client.send_message(message.channel, '{}: You rolled {}!'.format(message.author.name, rand))
        except:
            await client.send_message(message.channel,
                                      '{}: Could not roll with those parameters!'.format(message.author.name))

    elif message.content.startswith('!joined'):
        await client.delete_message(message)
        await client.send_message(message.channel, '{}: You joined the Ohm server {}!'.format(message.author.name,
                                                                                              message.author.joined_at))

    elif message.content.startswith('!ask'):
        question = message.content[5:]
        try:
            await client.send_message(message.channel, cb.ask(question))
        except Exception as e:
            print(e)
            await client.send_message(message.channel, '{}: That is not a question I will answer!'.format(message.author.name))

    elif message.content.startswith('!join'):
        await client.delete_message(message)
        if message.author not in ohm.split_list:
            ohm.split_list.append(message.author)
            await client.send_message(message.channel,
                                      '{}: You have joined the queue!\n'
                                      'Current queue: {}'.format(message.author.name, ohm.print_queue()))

    elif message.content.startswith('!split'):
        await client.delete_message(message)
        try:
            num_teams = int(message.content[7:])
        except:
            await client.send_message(message.channel,
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

    elif message.content.split('!cleanup'):
        await client.delete_message(message)
        team_number = 1
        while True:
            channel = discord.utils.get(message.author.server.channels, name='Team {}'.format(team_number))
            if channel is None:
                break
            else:
                await client.delete_channel(channel)
            team_number += 1

@client.event
async def on_voice_state_update(before, after):
    if after.voice_channel is None or after.is_afk:
        return
    if before.name is not None and before.name in ohm.intro_names \
            and before.voice_channel != after.voice_channel:
        if after.voice_channel.name != 'Supreme Ohhhhhmmmmmmm':
            for member in after.voice_channel.voice_members:
                if member.name in ohm.black_list:
                    return

        voice_client = client.voice_client_in(after.server)
        try:
            if voice_client is None:
                voice_client = await client.join_voice_channel(after.voice_channel)
            elif voice_client.channel != after.voice_channel:
                await voice_client.move_to(after.voice_channel)
        except Exception as e:
            print(e)
            return

        if ohm.active_player is not None and ohm.active_player.is_playing():
            ohm.active_player.stop()

        try:
            ohm.active_player = voice_client.create_ffmpeg_player('{}/intro.wav'.format(after.name))
            ohm.active_player.start()
        except Exception as e:
            print(e)

client.run('MTc2NDMzMTMwMzM1NTAyMzM3.CgvoFg.FLaupAZZ5OviZ1Fb7gAO_Aq-sLo')