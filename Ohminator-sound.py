import discord
import discord.channel
import discord.errors
import asyncio
import random
import cleverbot
import re
import os

client = discord.Client()

class Ohminator:
    active_player = None
    intro_player = None
    intro_playing = False
    intro_counter = 0
    intro_was_stopped = False
    intro_names = {'runarl', 'Rune', 'Chimeric', 'Johngel', 'Christian Berseth',
                   'Jan Ivar Ugelstad', 'Christian F. Vegard', 'Martin', 'Kristoffer Skau', 'Ginker', 'aekped',
                                                                                                      'sondrehav', 'Synspeckter'}
    black_list = {'Christian Berseth', 'Chimeric'}

    test_list = {'Rune', 'Chimeric', 'Christian Berseth', 'Martin'}

    help_message = '{}: List of sound commands: \n' \
                   '**!soundhelp**\t\t\t-\tPrints out this menu.\n' \
                   '**!yt** *[youtube link]*\t\t\t-\t  Plays audio from YouTube or other sources in voice channel of caller.\n' \
                   '**!stop** or **!stahp**\t\t\t\t\t\t\t\t  -\tStops playing sound from the yt player.\n' \
                   '**!pause**\t\t\t\t\t\t\t\t  -\tPauses playing sound from the yt player.\n' \
                   '**!resume**\t\t\t\t\t\t\t\t  -\tResumes playing sound from the yt player.\n' \
                   '**!skip**\t\t\t\t\t\t\t\t  -\tSkips to the next playing in the queue if one exists.\n' \
                   '**!q**\t\t\t\t\t\t\t\t  -\tLists the playlist queue.\n' \
                   '**!next**\t\t\t\t\t\t\t\t  -\tDisplays the next song in the queue.\n' \
                   '\n**Intro commands:**\n' \
                   '**!intro** *[(index)]*\t\t\t\t\t\t\t\t\t-\tPlays one of your intros at random. Can play intro at given index.\n' \
                   '**!introstop**\t\t\t\t\t\t\t\t  -\tStops playing the currently playing intro.\n' \
                   '**!myintros**\t\t\t\t\t\t\t\t\t-\tLists all of your intros.\n' \
                   '**!deleteintro** *[index]*\t\t\t\t\t\t\t\t\t-\tDeletes intro at given index.\n' \
                   '**!upload** *[url]*\t\t\t\-\tUploads a intro. File must be .wav and must be downloaded from Dropbox.\n' \
                   'The url must end on .wav. Example: https://www.dropbox.com/s/znt5tt3xe9vl8su/kekkk.wav. ' \
                   'Ending with ?dl=0 is not acceptable.'

    split_list = list()

    yt_playlist = list()
    play_next = asyncio.Event()

    bot_spam = None

    clear_now_playing = asyncio.Event()
    intro_finished = asyncio.Event()
    intro_counter_lock = asyncio.Lock()
    after_yt_lock = asyncio.Lock()

    def after_yt(self):
        client.loop.call_soon_threadsafe(self.clear_now_playing.set)
        client.loop.call_soon_threadsafe(self.play_next.set)
        print("YouTube-video finished playing.")

    def after_intro(self):
        client.loop.call_soon_threadsafe(self.intro_finished.set)
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

async def play_next_yt():
    while not client.is_closed:
        await ohm.play_next.wait()
        if len(ohm.yt_playlist) > 0:
            ohm.active_player = ohm.yt_playlist.pop(0)
            await client.change_status(discord.Game(name=ohm.active_player.title))
            await client.send_message(ohm.bot_spam,
                                      'Now playing: {}\nIt is {} seconds long'.format(ohm.active_player.title, ohm.active_player.duration))
            ohm.active_player.start()
        ohm.play_next.clear()

async def resume_playing_sound():
    while not client.is_closed:
        await ohm.intro_finished.wait()
        await ohm.intro_counter_lock.acquire()
        ohm.intro_counter -= 1
        if ohm.intro_counter == 0:
            if ohm.active_player is not None:
                ohm.active_player.resume()
        ohm.intro_counter_lock.release()
        ohm.intro_finished.clear()


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
    if message.content.startswith('!yt'):
        link = message.content[4:]
        await client.delete_message(message)

        if message.author.voice_channel is None or message.author.voice.is_afk:
            await client.send_message(ohm.bot_spam,
                                      '{}: Please join a voice channel to play your link!'.format(message.author.name))
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

        voice_client = client.voice_client_in(message.author.server)

        if ohm.intro_player is not None and ohm.intro_player.is_playing():
            if len(ohm.yt_playlist) > 0:
                try:
                    player = await voice_client.create_ytdl_player(link, options=option, after=ohm.after_yt)
                    await client.send_message(ohm.bot_spam,
                                              '{}: {} has been added to the queue.'.format(message.author.name,
                                                                                           player.title,
                                                                                           player.duration))
                    ohm.yt_playlist.append(player)
                except:
                    await client.send_message(ohm.bot_spam,
                                              '{}: Your link could not be played!'.format(message.author.name))
            else:
                try:
                    ohm.active_player = await voice_client.create_ytdl_player(link, options=option, after=ohm.after_yt)
                    await client.change_status(discord.Game(name=ohm.active_player.title))
                    await client.send_message(ohm.bot_spam,
                                              '{}: \nNow playing: {}\nIt is {} seconds long'.format(message.author.name,
                                                                                                    ohm.active_player.title,
                                                                                                    ohm.active_player.duration))
                    ohm.active_player.start()
                    ohm.active_player.pause()
                except:
                    await client.send_message(ohm.bot_spam,
                                              '{}: Your link could not be played!'.format(message.author.name))
            return

        if ohm.active_player is not None and (not ohm.active_player.is_done() or ohm.active_player.is_playing()):
            try:
                if voice_client is None:
                    voice_client = await client.join_voice_channel(message.author.voice_channel)
                elif voice_client.channel is None:
                    await voice_client.disconnect()
                    voice_client = await client.join_voice_channel(message.author.voice_channel)

            except:
                await client.send_message(ohm.bot_spam,
                                          '{}: Could not connect to voice channel!'.format(message.author.name))
                return
            try:
                player = await voice_client.create_ytdl_player(link, options=option, after=ohm.after_yt)
                await client.send_message(ohm.bot_spam,
                                          '{}: {} has been added to the queue.'.format(message.author.name, player.title, player.duration))
                ohm.yt_playlist.append(player)
            except:
                await client.send_message(ohm.bot_spam,
                                          '{}: Your link could not be played!'.format(message.author.name))
            return

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
            ohm.active_player = await voice_client.create_ytdl_player(link, options=option, after=ohm.after_yt)
            await client.change_status(discord.Game(name=ohm.active_player.title))
            await client.send_message(ohm.bot_spam,
                                      '{}: \nNow playing: {}\nIt is {} seconds long'.format(message.author.name,
                                                                                            ohm.active_player.title,
                                                                                            ohm.active_player.duration))
            ohm.active_player.start()
        except:
            await client.send_message(ohm.bot_spam, '{}: Your link could not be played!'.format(message.author.name))

    elif message.content.startswith('!pause'):
        await client.delete_message(message)
        if ohm.active_player is None or not ohm.active_player.is_playing():
            await client.send_message(ohm.bot_spam, '{}: Nothing to pause!'.format(message.author.name))
        else:
            await client.send_message(ohm.bot_spam, '{} paused the player!'.format(message.author.name))
            ohm.active_player.pause()

    elif message.content.startswith('!resume'):
        await client.delete_message(message)
        if ohm.active_player is None or not ohm.active_player.is_playing():
            await client.send_message(ohm.bot_spam, '{}: Nothing to resume!'.format(message.author.name))
        else:
            await client.send_message(ohm.bot_spam, '{} resumed the player!'.format(message.author.name))
            ohm.active_player.resume()

    elif message.content.startswith('!skip'):
        await client.delete_message(message)
        if ohm.active_player is None or not ohm.active_player.is_playing():
            await client.send_message(ohm.bot_spam, '{}: Nothing to skip!'.format(message.author.name))
        else:
            await client.send_message(ohm.bot_spam, '{} skipped the song!'.format(message.author.name))
            ohm.active_player.stop()

    elif message.content.startswith('!q'):
        await client.delete_message(message)
        if len(ohm.yt_playlist) > 0:
            cnt = 1
            queue = str()
            for play in ohm.yt_playlist:
                queue += "{}: {}\n".format(cnt, play.title)
                cnt += 1
            await client.send_message(ohm.bot_spam, '{}: Here is the current queue:\n{}'.format(message.author.name, queue.strip()))
        else:
            await client.send_message(ohm.bot_spam, '{}: There is nothing in the queue!'.format(message.author.name))

    elif message.content.startswith('!next'):
        await client.delete_message(message)
        if len(ohm.yt_playlist) > 0:
            await client.send_message(ohm.bot_spam,
                                      '{}: The next song is {}. It is {} seconds long'.format(message.author.name, ohm.yt_playlist[0].title, ohm.yt_playlist[0].duration))
        else:
            await client.send_message(ohm.bot_spam, '{}: There is no next song as the queue is empty!'.format(message.author.name))

    elif message.content.startswith('!stahp') or message.content.startswith('!stop'):
        await client.delete_message(message)
        if ohm.active_player is None or not ohm.active_player.is_playing():
            await client.send_message(ohm.bot_spam, '{}: No active player to stop!'.format(message.author.name))
        else:
            await client.send_message(ohm.bot_spam, '{} stopped the player and cleared the queue!'.format(message.author.name))
            ohm.yt_playlist.clear()
            ohm.active_player.stop()

    elif message.content.startswith('!introstop'):
        await client.delete_message(message)
        if ohm.intro_player is None or not ohm.intro_player.is_playing():
            await client.send_message(ohm.bot_spam, '{}: No active intro to stop!'.format(message.author.name))
        else:
            await client.send_message(ohm.bot_spam, '{} stopped the intro!'.format(message.author.name))
            ohm.intro_player.stop()
            print("Intro was stopped!")

    elif message.content.startswith('!intro'):
        await client.delete_message(message)
        if message.author.voice_channel is None or message.author.voice.is_afk:
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
                ohm.active_player.pause()

            if ohm.intro_player is not None and ohm.intro_player.is_playing():
                # await ohm.intro_counter_lock.acquire()
                # ohm.intro_counter -= 1
                ohm.intro_player.stop()
                # ohm.intro_counter_lock.release()

            try:
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

    elif message.content.startswith('!soundhelp'):
        await client.delete_message(message)
        await client.send_message(ohm.bot_spam, ohm.help_message.format(message.author.name))


@client.event
async def on_voice_state_update(before, after):
    if after.voice_channel is None or after.voice.is_afk:
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
            ohm.active_player.pause()

        if ohm.intro_player is not None and ohm.intro_player.is_playing():
            #await ohm.intro_counter_lock.acquire()
            #ohm.intro_counter -= 1
            ohm.intro_player.stop()
            #ohm.intro_counter_lock.release()

        try:
            intro_list = os.listdir('{}/intros'.format(after.name))
            ohm.intro_player = voice_client.create_ffmpeg_player(
                '{}/intros/{}'.format(after.name, random.choice(intro_list)), after=ohm.after_intro)
            ohm.intro_player.start()
            await ohm.intro_counter_lock.acquire()
            ohm.intro_counter += 1
            ohm.intro_counter_lock.release()
        except Exception as e:
            print(e)

client.loop.create_task(play_next_yt())
client.loop.create_task(should_clear_now_playing())
client.loop.create_task(resume_playing_sound())
client.run('MTc2NDMzMTMwMzM1NTAyMzM3.CgvoFg.FLaupAZZ5OviZ1Fb7gAO_Aq-sLo')

