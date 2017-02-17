import utils
import os
import random
import re
import urllib.request
import os.path
import shutil

async def introstop(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    if server.intro_player is None or not server.intro_player.is_playing():
        await client.send_message(bot_channel, '{}: No active intro to stop!'.format(message.author.name))
    else:
        await client.send_message(bot_channel, '{} stopped the intro!'.format(message.author.name))
        server.intro_player.stop()

async def intro(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    if message.author.voice_channel is None or message.author.voice.is_afk:
        return

    member = server.get_member(message.author.id)
    if message.author.name is not None and member.has_intro:

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
            await client.send_message(bot_channel,
                                      '{}: Could not connect to voice channel!'.format(message.author.name))
            return

        if server.active_player is not None and server.active_player.is_playing():
            server.active_player.pause()

        if server.intro_player is not None and server.intro_player.is_playing():
            server.intro_player.stop()

        try:
            intro_list = os.listdir('servers/{}/members/{}/intros'.format(server.server_loc, member.member_loc))
            try:
                given_index = int(message.content[6:])
                if given_index < 1:
                    # Because lists in python interprets negative indices as positive ones
                    # I give the intro index a high number to trigger the IndexError.
                    intro_index = 256
                else:
                    intro_index = given_index - 1
            except ValueError:
                intro_index = intro_list.index(random.choice(intro_list))
                given_index = 0

            try:
                server.intro_player = voice_client.create_ffmpeg_player(
                    'servers/{}/members/{}/intros/{}'.format(server.server_loc, member.member_loc,
                                                             intro_list[intro_index]),
                    after=server.intro_manager.after_intro)
            except IndexError:
                await client.send_message(bot_channel,
                                          '{}: The given index of {} is out of bounds!'.format(
                                              message.author.name, given_index))
                raise IndexError
            await server.intro_manager.intro_counter_lock.acquire()
            server.intro_manager.intro_counter += 1
            server.intro_manager.intro_counter_lock.release()
            server.intro_player.volume = 0.25
            server.intro_player.start()
        except IndexError:
            pass
        except NameError:
            pass
        except Exception as e:
            print(e)
            await client.send_message(bot_channel,
                                      '{}: Could not play intro!'.format(message.author.name))
        return
    else:
        await client.send_message(bot_channel,
                                  '{}: You dont have an intro!'.format(message.author.name))

async def myintros(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    member = server.get_member(message.author.id)
    intro_list = os.listdir('servers/{}/members/{}/intros'.format(server.server_loc, member.member_loc))
    intro_print = str()
    index_cnt = 1
    for i in intro_list:
        intro_print += '\n**[{}]**:\t{}'.format(index_cnt, i)
        index_cnt += 1
    await client.send_message(bot_channel,
                              '{}: Intro list:{}'.format(message.author.mention, intro_print))

async def deleteintro(message, bot_channel, client):
    await client.delete_message(message)
    try:
        intro_index = int(message.content[12:])
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
        member = server.get_member(message.author.id)
        intro_list = os.listdir('servers/{}/members/{}/intros'.format(server.server_loc, member.member_loc))
        await client.send_message(bot_channel,
                                  '{}: Deleting intro {} at index {}'.format(
                                      message.author.name, intro_list[intro_index - 1], intro_index))
        os.remove(
            'servers/{}/members/{}/intros/{}'.format(server.server_loc, member.member_loc, intro_list[intro_index - 1]))
    except:
        await client.send_message(bot_channel,
                                  '{}: Could not remove file. No file found at given index.'.format(
                                      message.author.name))
        return

async def old_upload(message, bot_channel, client):
    await client.delete_message(message)
    url = message.content[8:]
    try:
        find_name = re.findall(r'/([a-zA-z\d]+?.wav).*?$', url)
        file_name = find_name.pop()
    except:
        await client.send_message(bot_channel, '{}: Invalid file.'.format(message.author.name))
        return
    server = utils.get_server(message.server)
    member = server.get_member(message.author.id)
    intro_list = os.listdir('servers/{}/members/{}/intros'.format(server.server_loc, member.member_loc))
    if (len(intro_list) + 1) > 3:
        await client.send_message(bot_channel,
                                  '{}: You have reached the maximum number of intros. '
                                  'Please delete an intro before uploading a new one'.format(
                                      message.author.name))
        return
    url += '?dl=1&pv=1'

    file, header = urllib.request.urlretrieve(url)
    path = os.path.realpath(file)
    os.rename(path, 'servers/{}/members/{}/intros/{}'.format(server.server_loc, member.member_loc, file_name))
    await client.send_message(bot_channel, '{}: Upload successful.'.format(message.author.name))

async def upload(message, bot_channel, client):
    if len(message.attachments) > 0:
        try:
            # regex function checks if the file is a file ending with .wav or .mp3
            find_name = re.findall(r'([a-zA-Z\d_ .]+?.(?:wav|mpg))$', message.attachments[0]["filename"])
            file_name = find_name.pop()
        except IndexError:
            await client.send_message(bot_channel, '{}: Invalid file or file format. Must be .wav or .mpg.'.format(message.author.name))
            return

        server = utils.get_server(message.server)
        member = server.get_member(message.author.id)
        intro_list = os.listdir('servers/{}/members/{}/intros'.format(server.server_loc, member.member_loc))
        if (len(intro_list) + 1) > 3:
            await client.send_message(bot_channel,
                                      '{}: You have reached the maximum number of intros. '
                                      'Please delete an intro before uploading a new one'.format(
                                          message.author.name))
            return

        req = urllib.request.Request(message.attachments[0]["url"], headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(message.attachments[0]["filename"], 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        path = os.path.realpath(message.attachments[0]["filename"])
        os.rename(path, 'servers/{}/members/{}/intros/{}'.format(server.server_loc, member.member_loc, message.attachments[0]["filename"]))
        #TODO: Fix restrictions and check for valid file
        await client.delete_message(message)
        await client.send_message(bot_channel, '{}: Upload successful.'.format(message.author.name))
    else:
        await client.send_message(bot_channel, '{}: Please use this command while uploading a file to discord.'.format(message.author.name))
