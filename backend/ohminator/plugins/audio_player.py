import math
import random
import time
import traceback

import youtube_dl

from playlist import Playlist
from utils import RegisterCommand, playlists, create_now_playing_embed, update_active_player

from firebase_admin import db


@RegisterCommand("yt", "play", "p")
async def play_from_internet(message, bot_channel, client, guild_ref):
    await message.delete()
    output_channel = bot_channel
    guild = message.guild

    if len(message.content.split()) < 2:
        await output_channel.send(f'{message.author.name}: Usage: !yt or !play or !p [link or search term]')
        return

    link_or_phrase = " ".join(message.content.split()[1:])

    # The user must be in a channel to play their link.
    if message.author.voice is None or message.author.voice.afk:
        await output_channel.send(f'{message.author.name}: Please join a voice channel to play your link!')
        return

    # Restricts users to only be able to add songs to playlist if they are in the channel the bot is locked to.
    # This only applies if the player is locked to a channel.
    summoned_channel = message.guild.get_channel(guild_ref.get("summoned_channel"))
    if summoned_channel:
        if message.author.voice.channel == summoned_channel:
            voice_channel = summoned_channel
        else:
            await output_channel.send(f'{message.author.name}: '
                                      f'The bot is locked to channel {summoned_channel.name}. '
                                      'Please join that channel to make Ohminator play audio.')
            return
    else:
        voice_channel = message.author.voice.channel

    # Move if connected with a voice_client. Otherwise, we are not connected to voice and must connect.
    if message.guild.voice_client:
        await message.guild.voice_client.move_to(voice_channel)
    else:
        await voice_channel.connect()

    # Three cases: Case one: An intro is currently playing, so we either append or pause the active player.
    # Case two: Something is already playing, so we queue the requested songs
    # Case three: Nothing is playing, so we just start playing the song
    if str(guild.id) not in playlists:
        playlists[str(guild.id)] = Playlist(client, guild)

    playlist = playlists[str(guild.id)]

    await playlist.playlist_lock.acquire()

    guilds_ref = db.reference("guilds").child(f"{guild.id}")
    current_active_player = guilds_ref.child("active_player").get()
    if not current_active_player:
        current_active_player = {}

    async def start_player():
        audio_source = await playlist.add_to_playlist(link_or_phrase, False, message.author.name,
                                                      output_channel, message.author.name)
        playlist.now_playing = audio_source.title
        await output_channel.send(f'{message.author.name}:',
                                  embed=create_now_playing_embed(
                                      update_active_player(audio_source, db.reference(f"guilds/{guild.id}"),
                                                           message.author.name))
                                  )
        playlist.active_audio_source = audio_source
        message.guild.voice_client.play(audio_source, after=playlist.after_yt)

    try:
        # Must check if intro is already playing
        if current_active_player and current_active_player["type"] == "intro" \
                and current_active_player["status"] == "playing":
            # Check if there's something in the playlist
            if current_active_player.get("queue"):
                await playlist.add_to_playlist(link_or_phrase, True, message.author.name,
                                               output_channel, message.author.name)
            else:
                await start_player()
                message.guild.voice_client.pause()

        elif current_active_player and message.guild.voice_client.is_playing() or current_active_player.get("queue"):
            await playlist.add_to_playlist(link_or_phrase, True, message.author.name,
                                           output_channel, message.author.name)
        else:
            # Move to the user's voice channel
            if message.guild.voice_client.channel != voice_channel:
                await message.guild.voice_client.move_to(voice_channel)
            await start_player()

    except youtube_dl.utils.UnsupportedError:
        await output_channel.send(f'{message.author.name}: Unsupported URL: That URL is not supported! :slight_frown:')
    except youtube_dl.utils.DownloadError:
        await output_channel.send(f'{message.author.name}: Download Error: '
                                  f'Your link could not be downloaded! :slight_frown:')
    except youtube_dl.utils.MaxDownloadsReached:
        await output_channel.send(f'{message.author.name}: Max downloads reached: '
                                  f'Can not download more videos from YT at the moment. '
                                  'Please wait a moment before trying again. :slight_frown:')
    except youtube_dl.utils.UnavailableVideoError:
        await output_channel.send(f'{message.author.name}: The video is unavailable.')
    except:
        await output_channel.send(f'{message.author.name}: Your link could not be played!')
        traceback.print_exc()
    finally:
        playlist.playlist_lock.release()


@RegisterCommand("repeat", "again", "a")
async def repeat(message, bot_channel, client, guild_ref):
    await message.delete()
    voice_client = message.guild.voice_client
    if voice_client is None or (not voice_client.is_paused() and not voice_client.is_playing()):
        await message.channel.send(f'{message.author.name}: Nothing to repeat!')
    else:
        active_player_ref = db.reference(f"guilds/{message.guild.id}/active_player")
        current_active_player = active_player_ref.get()
        await message.channel.send(f':repeat: {message.author.name} repeated {current_active_player["title"]}.')
        queue = current_active_player.get('queue', [])
        queue.insert(0, {"title": current_active_player["title"], "link": current_active_player["link"],
                         "duration": current_active_player["duration"],
                         "thumbnail": current_active_player["thumbnail"], "user": current_active_player["user"]})
        active_player_ref.update({"queue": queue})


@RegisterCommand("shuffle", "sh")
async def shuffle(message, bot_channel, client, guild_ref):
    await message.delete()
    voice_client = message.guild.voice_client
    if voice_client is None or (not voice_client.is_paused() and not voice_client.is_playing()):
        await message.channel.send(f'{message.author.name}: Nothing to shuffle!')
    else:
        await message.channel.send(f':twisted_rightwards_arrows: {message.author.name} shuffled the list.')
        active_player_ref = db.reference(f"guilds/{message.guild.id}/active_player")
        current_active_player = active_player_ref.get()
        queue = current_active_player.get("queue", [])
        random.shuffle(queue)
        queue.sort(key=lambda element: len(element.get('vote_list', [])), reverse=True)
        active_player_ref.update({"queue": queue})


@RegisterCommand("pause", "pa")
async def pause(message, bot_channel, client, guild_ref):
    await message.delete()
    voice_client = message.guild.voice_client
    if voice_client is None or (not voice_client.is_paused() and not voice_client.is_playing()):
        await bot_channel.send(f'{message.author.name}: Nothing to pause!')
    elif voice_client.is_paused():
        await bot_channel.send(f'{message.author.name}: The player is already paused!')
    else:
        await bot_channel.send(f':pause_button:: {message.author.name} paused the player!')
        #server.active_playlist_element.pause_time = time.time()
        voice_client.pause()
        db.reference(f"guilds/{message.guild.id}/active_player").update({"status": "paused"})


@RegisterCommand("resume", "r")
async def resume(message, bot_channel, client, guild_ref):
    await message.delete()
    voice_client = message.guild.voice_client
    if voice_client is None or (not voice_client.is_paused() and not voice_client.is_playing()):
        await bot_channel.send(f'{message.author.name}: Nothing to resume!')
    else:
        await bot_channel.send(f':arrow_forward:: {message.author.name} resumed the player!')
        #server.active_playlist_element.start_time += (server.active_playlist_element.pause_time-server.active_playlist_element.start_time)
        voice_client.resume()
        db.reference(f"guilds/{message.guild.id}/active_player").update({"status": "playing"})


@RegisterCommand("volume", "sv")
async def volume(message, bot_channel, client, guild_ref):
    await message.delete()
    voice_client = message.guild.voice_client
    if voice_client is None or (not voice_client.is_paused() and not voice_client.is_playing()):
        await bot_channel.send(f'{message.author.name}: Nothing is playing!')
    else:
        parameters = message.content.split()
        if len(parameters) < 2:
            current_volume = voice_client.source.volume
        else:
            try:
                current_volume = float(parameters[1])/2/100.0
            except ValueError:
                await bot_channel.send(f'{message.author.name}: Please give a numeric value!')
                return

        if current_volume <= 0.0:
            icon = ':mute:'
        elif 0.0 < current_volume < 0.15:
            icon = ':speaker:'
        elif 0.14 < current_volume < 0.35:
            icon = ':sound:'
        else:
            icon = ':loud_sound:'

        if len(parameters) < 2:
            await bot_channel.send(f'{icon}: {message.author.name}, '
                                       f'the volume for the current track is {int(current_volume*2*100.0)}%!')
        elif parameters[1] == current_volume:
            await bot_channel.send(f'{icon}: {message.author.name}, the volume is already the given value!')
        else:
            if current_volume < 0.0:
                current_volume = 0.0
            elif current_volume > 0.5:
                current_volume = 0.5

            await bot_channel.send(f'{icon}: {message.author.name}, the volume was changed from '
                                       f'{int(voice_client.source.volume*2*100.0)}% to '
                                       f'{int(current_volume*2*100.0)}%!')
            voice_client.source.volume = current_volume
            db.reference(f"guilds/{message.guild.id}/active_player").update({"volume": current_volume})


@RegisterCommand("delete", "d", "remove")
async def delete(message, bot_channel, client, guild_ref):
    await message.delete()
    parameters = message.content.split()
    try:
        index = int(parameters[1]) - 1
    except ValueError:
        await message.channel.send(f'{message.author.name}: Please give a numeric value!')
        return
    except IndexError:
        await message.channel.send(f'{message.author.name}: Please give an index to delete!')
        return

    try:
        queue = db.reference(f"guilds/{message.guild.id}/active_player/queue").get()
        title = queue[index]['title']
        del queue[index]
        db.reference(f"guilds/{message.guild.id}/active_player").update({"queue": queue})
        await message.channel.send(f"{message.author.name}: Entry \'{title}\' "
                                   f"with index {index+1} was deleted from the queue.")
    except IndexError:
        await message.channel.send(f'{message.author.name}: Index {index+1} is out of queue bounds!')


@RegisterCommand("skip", "sk")
async def skip(message, bot_channel, client, guild_ref):
    await message.delete()
    if str(message.guild.id) not in playlists:
        playlists[str(message.guild.id)] = Playlist(client, message.guild, guild_ref)

    playlist = playlists[str(message.guild.id)]

    voice_client = message.guild.voice_client

    await playlist.playlist_lock.acquire()
    guilds_ref = db.reference("guilds").child(f"{message.guild.id}")
    current_active_player = guilds_ref.child("active_player").get()
    try:
        if voice_client is None or (not voice_client.is_paused() and not voice_client.is_playing()) \
                and current_active_player and not current_active_player.get("queue"):
            await bot_channel.send(f'{message.author.name}: Nothing to skip!')
        else:
            await bot_channel.send(f':track_next:: {message.author.name} skipped the song!')
            voice_client.stop()
    finally:
        playlist.playlist_lock.release()


@RegisterCommand("next", "n")
async def next(message, bot_channel, client, guild_ref):
    await message.delete()
    queue = db.reference(f"guilds/{message.guild.id}/active_player/queue")
    if queue:
        await message.channel.send(f'{message.author.name}: The next song is {queue[0]["title"]}.')
    else:
        await message.channel.send(f'{message.author.name}: There is no next song as the queue is empty!')


@RegisterCommand("stop", "s", "stahp", "stap")
async def stop(message, bot_channel, client, guild_ref):
    await message.delete()
    voice_client = message.guild.voice_client
    if voice_client and voice_client.is_playing() and not voice_client.is_paused():
        voice_client.stop()
        db.reference(f"guilds/{message.guild.id}/active_player").delete()
        await bot_channel.send(f':stop_button:: {message.author.name} stopped the player and cleared the queue!')
    else:
        await bot_channel.send(f'{message.author.name}: No active player to stop!')


@RegisterCommand("yttop", "playtop", "pt")
async def play_on_top(message, bot_channel, client, guild_ref):
    await play_from_internet(message, bot_channel, client, guild_ref)
    # If the queue is not empty, the last entry must be what was added last.
    # It should not be a race condition as we're not awaiting anything.
    queue = db.reference(f"guilds/{message.guild.id}/active_player/queue").get()
    if queue:
        queue.insert(0, queue[-1])
        db.reference(f"guilds/{message.guild.id}/active_player").update({"queue": queue})


@RegisterCommand("queue", "q", "queuepage")
async def queue_page(message, bot_channel, client, guild_ref):
    await message.delete()
    queue = db.reference(f"guilds/{message.guild.id}/active_player/queue").get()
    if not queue:
        await bot_channel.send(f'{message.author.name}: There is nothing in the queue!')
        return

    parameters = message.content.split()
    try:
        index = int(parameters[1]) - 1
        if not 0 <= index < len(queue):
            await bot_channel.send(f'{message.author.name}: Index {index + 1} is out of queue bounds!')
        else:
            await print_from_index(index, message, client)
    except ValueError:
        await bot_channel.send(f'{message.author.name}: Please give a numeric value!')
    except IndexError:
        queue_pages = QueuePage()
        await queue_pages.print_next_page(client, message.channel)


async def print_from_index(index, message, client):
    queue = db.reference(f"guilds/{message.guild.id}/active_player/queue").get()
    queue_str = str()
    try:
        for i in range(index, index + 30, 1):
            votes = ''
            if len(queue[i].get("vote_list", [])) > 0:
                votes = f' **[{len(queue[i].get("vote_list", []))}]**'
            queue_str += f"{i + 1}: {queue[i]['title']}{votes}\n"
        queue_str += f"Total entries: {len(queue)}\n"
    except IndexError:
        queue_str += "End of queue!"
    await message.channel.send(f'{message.author.name}: '
                               f'Here is the current queue from index {index+1}:\n{queue_str.strip()}')


class QueuePage:
    def __init__(self):
        self.page_num = 0
        self.message = None
        self.end = False

    async def print_next_page(self, client, channel):
        if self.end:
            return
        queue = db.reference(f"guilds/{channel.guild}/active_player/queue").get()
        queue_str = str()
        try:
            for i in range(self.page_num*30, (self.page_num*30)+30, 1):
                votes = ''
                if len(queue[i].get("vote_list", [])) > 0:
                    votes = f' **[{len(queue[i].get("vote_list", []))}]**'
                queue_str += f"{i+1}: {queue[i]['title']}{votes}\n"

            pages_left = math.ceil((len(queue)-((self.page_num*30)+29))/30)
            queue_str += f"Total entries: {len(queue)}\n"
            if pages_left > 0:
                queue_str += f"There {pages_left == 1 and 'is' or 'are'} {pages_left} " \
                             f"{pages_left == 1 and 'page' or 'pages'} left"
        except IndexError:
            queue_str += "End of queue!"
            self.end = True

        self.page_num += 1
        if self.message is None:
            self.message = await channel.send(f'Here is the current queue:\n{queue_str.strip()}')
        else:
            await self.message.edit(f'Here is the current queue:\n{queue_str.strip()}')


@RegisterCommand("vote", "v")
async def vote(message, bot_channel, client, guild_ref):
    await message.delete()
    parameters = message.content.split()
    try:
        index = int(parameters[1]) - 1
    except ValueError:
        await message.channel.send(f'{message.author.name}: Please give a numeric value!')
        return
    except IndexError:
        await message.channel.send(f'{message.author.name}: Please give an index to vote for!')
        return

    try:
        queue = db.reference(f"guilds/{message.guild.id}/active_player/queue").get()
        queue_element = queue[index]
        vote_list = queue_element.get('vote_list', [])
        if message.author.id in vote_list:
            await message.channel.send(f'{message.author.name}: You can only vote once on one entry!')
            return
        vote_list.append(message.author.id)
        queue[index]['vote_list'] = vote_list
        for element in queue:
            if len(element.get(vote_list, [])) < len(vote_list):
                queue.remove(queue_element)
                queue.insert(queue.index(element), queue_element)
                break
        db.reference(f"guilds/{message.guild.id}/active_player").update({"queue": queue})
        await message.channel.send(f'{message.author.name}: {queue_element["title"]} has been voted for!')

    except IndexError:
        await message.channel.send(f'{message.author.name}: Index {index+1} is out of queue bounds!')
