import os
import os.path
import random
import re
import shutil
import traceback
import urllib.request
import asyncio

from discord import FFmpegPCMAudio
from firebase_admin import storage, db
from google.cloud.exceptions import NotFound

from playlist import Playlist
from utils import RegisterCommand, playlists


class IntroManager:
    def __init__(self, client, ohm_server):
        self.client = client
        self.ohm_server = ohm_server
        self.intro_counter = 0
        self.intro_finished = asyncio.Event()
        self.intro_counter_lock = asyncio.Lock()
        self.intro_lock = asyncio.Lock()


@RegisterCommand("intro", "i")
async def intro(message, bot_channel, client, guild_ref):
    await message.delete()

    if message.author.voice is None or message.author.voice.afk:
        return

    bucket = storage.bucket()

    blobs = list(bucket.list_blobs(prefix=f"guilds/{message.guild.id}/intros/{message.author.id}/", delimiter="/"))
    if blobs:
        if str(message.guild.id) not in playlists:
            playlists[str(message.guild.id)] = Playlist(client, message.guild)

        playlist = playlists[str(message.guild.id)]

        given_index = 0
        try:
            try:
                parameters = message.content.split()
                if len(parameters) > 1:
                    given_index = int(parameters[1])
                    if given_index < 1:
                        # Because negative indices are valid in python,
                        # but not in our use case, we throw an error here
                        raise IndexError
                    else:
                        intro_index = given_index - 1
                else:
                    raise ValueError
            except ValueError:
                intro_index = blobs.index(random.choice(blobs))
                given_index = 0

            blobs[intro_index].download_to_filename('intro.mp3')
            with open("intro.mp3", 'r') as f:
                audio_source = FFmpegPCMAudio(f, pipe=True, options='-loglevel quiet')

            # Move if connected with a voice_client. Otherwise, we are not connected to voice and must connect.
            if message.guild.voice_client:
                await message.guild.voice_client.move_to(message.author.voice.channel)
            else:
                await message.author.voice.channel.connect()

            message.guild.voice_client.pause()

            def after_intro(error):
                if playlist.active_audio_source:
                    message.guild.voice_client.play(playlist.active_audio_source, after=playlist.after_yt)

            message.guild.voice_client.play(audio_source, after=after_intro)
        except IndexError:
            await bot_channel.send(f'{message.author.name}: The given index of {given_index} is out of bounds!')
        except NameError:
            pass
        except Exception as e:
            print(e)
            await bot_channel.send(f'{message.author.name}: Could not play intro!')
        finally:
            pass
    else:
        await client.send_message(bot_channel, f'{message.author.name}: You dont have an intro!')


async def on_voice_state_update(self, member, before, after):
    if member.id == self.user.id:
        return

    if after is None or after.channel is None or after.afk or before is after:
        return

    bucket = storage.bucket()
    blobs = list(bucket.list_blobs(prefix=f"guilds/{member.guild.id}/intros/{member.id}/", delimiter="/"))
    if not blobs:
        return

    if str(member.guild.id) not in playlists:
        playlists[str(member.guild.id)] = Playlist(self, member.guild)

    playlist = playlists[str(member.guild.id)]

    blobs[blobs.index(random.choice(blobs))].download_to_filename('intro.mp3')
    with open("intro.mp3", 'r') as f:
        audio_source = FFmpegPCMAudio(f, pipe=True, options='-loglevel quiet')

    # Move if connected with a voice_client. Otherwise, we are not connected to voice and must connect.
    if member.guild.voice_client:
        await member.guild.voice_client.move_to(member.voice.channel)
    else:
        await member.voice.channel.connect()

    member.guild.voice_client.pause()

    def after_intro(error):
        if playlist.active_audio_source:
            member.guild.voice_client.play(playlist.active_audio_source, after=playlist.after_yt)

    member.guild.voice_client.play(audio_source, after=after_intro)


@RegisterCommand("myintros", "intros", "mi")
async def myintros(message, bot_channel, client, guild_ref):
    await message.delete()
    bucket = storage.bucket()
    blobs = list(bucket.list_blobs(prefix=f"guilds/{message.guild.id}/intros/{message.author.id}/", delimiter="/"))
    intro_print = str()
    index_cnt = 1
    for i in blobs:
        intro_print += f'\n**[{index_cnt}]**:\t{i.name.split("/")[-1]}'
        index_cnt += 1
    await bot_channel.send(f'{message.author.mention}: Intro list:{intro_print}')


@RegisterCommand("deleteintro", "introdelete")
async def deleteintro(message, bot_channel, client, guild_ref):
    await message.delete()
    parameters = message.content.split()
    try:
        if len(parameters) < 2:
            raise Exception
        intro_index = int(parameters[1])
        if intro_index < 1 or intro_index > 5:
            await bot_channel.send(f'{message.author.name}: Index is out of bounds!')
            return
    except (IndexError, TypeError, Exception):
        await bot_channel.send(f'{message.author.name}: Invalid parameter. Must be the index of the intro to delete!')
        return

    try:
        bucket = storage.bucket()
        blobs = list(bucket.list_blobs(prefix=f"guilds/{message.guild.id}/intros/{message.author.id}/", delimiter="/"))
        await bot_channel.send(f'{message.author.name}: '
                               f'Deleting intro {blobs[intro_index - 1].name.split("/")[-1]} at index {intro_index}')
        blobs[intro_index - 1].delete()
    except IndexError:
        await bot_channel.send(f'{message.author.name}: Could not remove file. No file found at given index.')


@RegisterCommand("upload", "up", "u")
async def upload(message, bot_channel, client, guild_ref):
    if len(message.attachments) > 0:
        attachment = message.attachments[0]
        try:
            # regex function checks if the file is a file ending with .wav or .mp3
            find_name = re.findall(r'([a-zA-Z\d_ .]+?.(?:wav|mp3))$', attachment.filename)
            file_name = find_name.pop()
        except IndexError:
            await bot_channel.send(f'{message.author.name}: Invalid file or file format. Must be .wav or .mp3.')
            return

        bucket = storage.bucket()
        blobs = list(bucket.list_blobs(prefix=f"guilds/{message.guild.id}/intros/{message.author.id}/", delimiter="/"))
        if len(blobs) > 3:
            await bot_channel.send(
                f'{message.author.name}: You have reached the maximum number of intros. '
                'Please delete an intro before uploading a new one')
            return

        req = urllib.request.Request(attachment.url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            blob = bucket.blob(f"guilds/{message.guild.id}/intros/{message.author.id}/{attachment.filename}")
            blob.upload_from_string(response.read(), content_type=response.headers["Content-Type"])
        #TODO: Fix restrictions and check for valid file
        await message.delete()
        await bot_channel.send(f'{message.author.name}: Upload successful.')
    else:
        await bot_channel.send(f'{message.author.name}: Please use this command while uploading a file to discord.')


@RegisterCommand("defaultintro", "di")
async def default_intro(message, bot_channel, client):
    await message.delete()
    server = utils.get_server(message.server)
    if message.author.voice_channel is None or message.author.voice.is_afk:
        return

    member = server.get_member(message.author.id)
    if message.author.name is not None and member.has_intro:
        # Handles playing intros when the bot is summoned
        if server.playlist.summoned_channel:
            if message.author.voice.voice_channel == server.playlist.summoned_channel:
                voice_channel = server.playlist.summoned_channel
            else:
                await client.send_message(bot_channel,
                                          '{}: The bot is locked to channel {}. '
                                          'Please join that channel to use !intro.'.format(
                                              message.author.name, server.playlist.summoned_channel.name))
                return
        else:
            voice_channel = message.author.voice_channel

        voice_client = client.voice_client_in(message.author.server)
        try:
            if voice_client is None:
                voice_client = await client.join_voice_channel(voice_channel)
            elif voice_client.channel is None:
                await voice_client.disconnect()
                voice_client = await client.join_voice_channel(voice_channel)
            elif voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)
        except Exception as e:
            print(e)
            await client.send_message(bot_channel,
                                      '{}: Could not connect to voice channel!'.format(message.author.name))
            return

        if server.active_tts:
            server.active_tts.stop()
            server.tts_queue.clear()

        if server.active_player is not None and server.active_player.is_playing():
            server.active_player.pause()

        if server.intro_player is not None and server.intro_player.is_playing():
            server.intro_player.stop()

        given_index = 0
        try:
            intro_list = os.listdir('servers/{}/default_intros'.format(server.server_loc))
            if len(intro_list) == 0:
                await client.send_message(bot_channel,
                                          '{}: No default intros have been added!'.format(message.author.name))
                return
            try:
                parameters = message.content.split()
                if len(parameters) > 1:
                    given_index = int(parameters[1])
                    if given_index < 1:
                        # Because negative indices are valid in python,
                        # but not in our use case, we throw an error here
                        raise IndexError
                    else:
                        intro_index = given_index - 1
                else:
                    raise ValueError
            except ValueError:
                intro_index = intro_list.index(random.choice(intro_list))
                given_index = 0

            server.intro_player = voice_client.create_ffmpeg_player(
                'servers/{}/default_intros/{}'.format(server.server_loc, intro_list[intro_index]),
                after=server.intro_manager.after_intro)
            await server.intro_manager.intro_counter_lock.acquire()
            server.intro_manager.intro_counter += 1
            server.intro_player.volume = 0.25
            server.intro_player.start()
        except IndexError:
            await client.send_message(bot_channel,
                                      '{}: The given index of {} is out of bounds!'.format(
                                          message.author.name, given_index))
        except NameError:
            pass
        except Exception as e:
            print(e)
            await client.send_message(bot_channel,
                                      '{}: Could not play intro!'.format(message.author.name))
        finally:
            server.intro_manager.intro_counter_lock.release()
    else:
        await client.send_message(bot_channel,
                                  '{}: You dont have an intro!'.format(message.author.name))


@RegisterCommand("defaultintros", "dis", "ldi", "listdefaultintros")
async def list_default_intros(message, bot_channel, client):
    await message.delete()
    server = utils.get_server(message.server)
    intro_list = os.listdir('servers/{}/default_intros'.format(server.server_loc))
    intro_print = str()
    index_cnt = 1
    for i in intro_list:
        intro_print += '\n**[{}]**:\t{}'.format(index_cnt, i)
        index_cnt += 1
    await client.send_message(bot_channel,
                              '{}: Default intro list:{}'.format(message.author.mention, intro_print))


@RegisterCommand("deletedefaultintro", "ddi")
async def delete_default_intro(message, bot_channel, client):
    await message.delete()
    parameters = message.content.split()
    try:
        if len(parameters) < 2:
            raise Exception
        intro_index = int(parameters[1])
        if intro_index < 1 or intro_index > 5:
            await client.send_message(bot_channel,
                                      '{}: Index is out of bounds!'.format(message.author.name))
            return
    except:
        await client.send_message(bot_channel,
                                  '{}: Invalid parameter. Must be the index of the intro to delete!'.format(
                                      message.author.name))
        return

    try:
        server = utils.get_server(message.server)
        intro_list = os.listdir('servers/{}/default_intros'.format(server.server_loc))
        await client.send_message(bot_channel,
                                  '{}: Deleting default intro {} at index {}'.format(
                                      message.author.name, intro_list[intro_index - 1], intro_index))
        os.remove(
            'servers/{}/default_intros/{}'.format(server.server_loc, intro_list[intro_index - 1]))
    except:
        await client.send_message(bot_channel,
                                  '{}: Could not remove file. No file found at given index.'.format(
                                      message.author.name))
        return


@RegisterCommand("uploaddefaultintro", "udi")
async def upload_default_intro(message, bot_channel, client):
    if len(message.attachments) > 0:
        try:
            # regex function checks if the file is a file ending with .wav or .mp3
            find_name = re.findall(r'([a-zA-Z\d_ .]+?.(?:wav|mp3))$', message.attachments[0]["filename"])
            file_name = find_name.pop()
        except IndexError:
            await client.send_message(bot_channel, '{}: Invalid file or file format. Must be .wav or .mp3.'.format(
                message.author.name))
            return

        server = utils.get_server(message.server)
        intro_list = os.listdir('servers/{}/default_intros'.format(server.server_loc))
        if (len(intro_list) + 1) > 3:
            await client.send_message(bot_channel,
                                      '{}: You have reached the maximum number of default intros. '
                                      'Please delete an intro before uploading a new one.'.format(
                                          message.author.name))
            return

        req = urllib.request.Request(message.attachments[0]["url"], headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(message.attachments[0]["filename"], 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        path = os.path.realpath(message.attachments[0]["filename"])
        os.rename(path, 'servers/{}/default_intros/{}'.format(server.server_loc, message.attachments[0]["filename"]))
        # TODO: Fix restrictions and check for valid file
        await message.delete()
        await client.send_message(bot_channel, '{}: Upload successful.'.format(message.author.name))
    else:
        await client.send_message(bot_channel, '{}: Please use this command while uploading a file to discord.'.format(
            message.author.name))
