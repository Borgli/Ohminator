import discord
import discord.channel
import discord.errors
import asyncio
import random
import cleverbot
import time
import re
import os
import urllib
import urllib.request
import dropbox

client = discord.Client()

class Ohminator:
    active_player = None
    intro_names = {'runarl', 'Rune', 'Chimeric', 'Johngel', 'Christian Berseth',
                   'Jan Ivar Ugelstad', 'Christian F. Vegard', 'Martin', 'Kristoffer Skau', 'Ginker', 'aekped',
                                                                                                      'sondrehav'}
    black_list = {'Christian Berseth', 'Chimeric'}

    test_list = {'Rune', 'Chimeric', 'Christian Berseth', 'Martin'}

    help_message = '{}: List of commands: \n' \
                   '**!help** or **!command**\t\t\t-\tPrints out this menu.\n' \
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

    clear_now_playing = asyncio.Event()

    def after_yt(self):
        client.loop.call_soon_threadsafe(self.clear_now_playing.set)

        #yield from client.change_status(discord.Game())
        print("YoutTube-video finished playing.")

    def after_intro(self):
        print("Intro finished playing.")

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

async def should_clear_now_playing():
    while not client.is_closed:
        await ohm.clear_now_playing.wait()
        await client.change_status(discord.Game())
        ohm.clear_now_playing.clear()

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

    elif message.content.startswith('!yt'):
        link = message.content[4:]
        await client.delete_message(message)

        if message.author.voice_channel is None or message.author.is_afk:
            await client.send_message(ohm.bot_spam,
                                      '{}: Please join a voice channel to play your link!'.format(message.author.name))
            return

        if ohm.active_player is not None and ohm.active_player.is_playing():
            await client.send_message(ohm.bot_spam,
                                      '{}: Something is already playing!'.format(message.author.name))
            return

        voice_client = client.voice_client_in(message.author.server)
        try:
            if voice_client is None:
                voice_client = await client.join_voice_channel(message.author.voice_channel)
            elif voice_client.channel is None:
                await voice_client.disconnect()
                voice_client = await client.join_voice_channel(message.author.voice_channel)
            elif voice_client.channel != message.author.voice_channel:
                await voice_client.move_to(message.author.voice_channel)
        except:
            await client.send_message(ohm.bot_spam,
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

            seconds = int(to_convert[0])

            if seconds > 59:
                m, s = divmod(seconds, 60)
                h, m = divmod(m, 60)
                option = '-ss {}:{}:{}'.format(h, m, s)
            else:
                option = '-ss {}:{}:{}'.format(to_convert[2], to_convert[1], to_convert[0])
            print(option)
        except:
            option = None

        try:
            ohm.active_player = await voice_client.create_ytdl_player(link, options=option, after=ohm.after_yt)
            await client.change_status(discord.Game(name=ohm.active_player.title))
            await client.send_message(ohm.bot_spam,
                                      '{}: \nNow playing: {}\nIt is {} seconds long'.format(message.author.name,
                                                                                            ohm.active_player.title,
                                                                                            ohm.active_player.duration))
            ohm.active_player.start()
        except:
            await client.send_message(ohm.bot_spam, '{}: Your link could not be played!'.format(message.author.name))

    elif message.content.startswith('!stahp') or message.content.startswith('!stop'):
        await client.delete_message(message)
        if ohm.active_player is None or not ohm.active_player.is_playing:
            await client.send_message(ohm.bot_spam, '{}: No active player!'.format(message.author.name))
        else:
            await client.send_message(ohm.bot_spam, '{} stopped the player!'.format(message.author.name))
            ohm.active_player.stop()

    # elif message.content.startswith('!introlist') or message.content.startswith('!listintros'):
    #     await client.delete_message(message)
    #     name_of_member = message.content[12:]
    #     if name_of_member is "":
    #         await client.send_message(ohm.bot_spam,
    #                                   '{}: Please provide a member!'.format(
    #                                       message.author.name))
    #         return
    #     try:
    #         intro_list = os.listdir('{}/intros'.format(name_of_member))
    #     except:
    #         await client.send_message(ohm.bot_spam,
    #                                   '{}: Member "{}" does not have access to intros!'.format(
    #                                       message.author.name, name_of_member))
    #         return
    #
    #     intro_print = str()
    #     index_cnt = 1
    #     for intro in intro_list:
    #         intro_print += '\n**[{}]**:\t{}'.format(index_cnt, intro)
    #         index_cnt += 1
    #     await client.send_message(ohm.bot_spam,
    #                               '{}: Here is the intro list of "{}":{}'.format(message.author.mention, name_of_member,
    #                                                                              intro_print))

    elif message.content.startswith('!intro'):
        await client.delete_message(message)
        if message.author.voice_channel is None or message.author.is_afk:
            return

        if message.author.name is not None and message.author.name in ohm.intro_names:

            voice_client = client.voice_client_in(message.author.server)
            try:
                if voice_client is None:
                    voice_client = await client.join_voice_channel(message.author.voice_channel)
                elif voice_client.channel is None:
                    await voice_client.disconnect()
                    voice_client = await client.join_voice_channel(message.author.voice_channel)
                elif voice_client.channel != message.author.voice_channel:
                    await voice_client.move_to(message.author.voice_channel)
            except Exception as e:
                print(e)
                await client.send_message(ohm.bot_spam,
                                          '{}: Could not connect to voice channel!'.format(message.author.name))
                return

            if ohm.active_player is not None and ohm.active_player.is_playing():
                ohm.active_player.stop()

            try:
                if message.content.startswith('!introof'):
                    # match = re.match(r'!introof ([a-zA-Z\s]+)(\d*)', message.content)
                    # if match is None:
                    #     await client.send_message(ohm.bot_spam,
                    #                               '{}: USAGE: !introof [name of member] [(index of intro)]!'.format(
                    #                                   message.author.name))
                    #     return
                    # name_of_member = match.group(1).strip()
                    # if name_of_member is "":
                    #     await client.send_message(ohm.bot_spam,
                    #                               '{}: Please provide a member!'.format(
                    #                                   message.author.name))
                    #     return
                    #
                    # try:
                    #     intro_list = os.listdir('{}/intros'.format(name_of_member))
                    # except:
                    #     await client.send_message(ohm.bot_spam,
                    #                               '{}: Member "{}" does not have access to intros!'.format(
                    #                                   message.author.name, name_of_member))
                    #     raise NameError
                    #
                    # if len(match.groups()) > 2:
                    #     try:
                    #         given_index = int(match.group(2))
                    #         if given_index < 1:
                    #             # Because lists in python interprets negative indices as positive ones
                    #             # I give the intro index a high number to trigger the IndexError.
                    #             intro_index = 256
                    #         else:
                    #             intro_index = given_index-1
                    #     except ValueError:
                    #         intro_index = intro_list.index(random.choice(intro_list))
                    # else:
                    #     intro_index = intro_list.index(random.choice(intro_list))
                    #
                    # try:
                    #     ohm.active_player = voice_client.create_ffmpeg_player(
                    #         '{}/intros/{}'.format(name_of_member, intro_list[intro_index]), after=ohm.after_intro)
                    # except:
                    #     await client.send_message(ohm.bot_spam,
                    #                               '{}: Member "{}" does not have an intro!'.format(
                    #                                   message.author.name, name_of_member))
                    #     raise NameError
                    pass

                else:
                    intro_list = os.listdir('{}/intros'.format(message.author.name))
                    try:
                        given_index = int(message.content[6:])
                        if given_index < 1:
                            # Because lists in python interprets negative indices as positive ones
                            # I give the intro index a high number to trigger the IndexError.
                            intro_index = 256
                        else:
                            intro_index = given_index-1
                    except ValueError:
                        intro_index = intro_list.index(random.choice(intro_list))

                    try:
                        ohm.active_player = voice_client.create_ffmpeg_player(
                            '{}/intros/{}'.format(message.author.name, intro_list[intro_index]), after=ohm.after_intro)
                    except IndexError:
                        await client.send_message(ohm.bot_spam,
                                                  '{}: The given index of {} is out of bounds!'.format(
                                                      message.author.name, given_index))
                        raise IndexError

                ohm.active_player.start()
            except IndexError:
                pass
            except NameError:
                pass
            except Exception as e:
                print(e)
                await client.send_message(ohm.bot_spam,
                                          '{}: Could not play intro!'.format(message.author.name))
            return

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
            elif voice_client.channel is None:
                await voice_client.disconnect()
                voice_client = await client.join_voice_channel(after.voice_channel)
            elif voice_client.channel != after.voice_channel:
                await voice_client.move_to(after.voice_channel)
        except Exception as e:
            print(e)
            return

        if ohm.active_player is not None and ohm.active_player.is_playing():
            ohm.active_player.stop()

        try:
            intro_list = os.listdir('{}/intros'.format(after.name))
            ohm.active_player = voice_client.create_ffmpeg_player(
                '{}/intros/{}'.format(after.name, random.choice(intro_list)), after=ohm.after_intro)
            ohm.active_player.start()
        except Exception as e:
            print(e)

client.loop.create_task(should_clear_now_playing())

def run_client():
    try:
        client.run('MTc2NDMzMTMwMzM1NTAyMzM3.CgvoFg.FLaupAZZ5OviZ1Fb7gAO_Aq-sLo')
        return False
    except discord.errors.ConnectionClosed:
        return True

connection_error = True
while connection_error:
    connection_error = run_client()

