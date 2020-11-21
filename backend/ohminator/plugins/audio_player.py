import time
import traceback

import youtube_dl

from playlist import Playlist
from utils import RegisterCommand, playlists, create_now_playing_embed

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
            await output_channel.send_message(f'{message.author.name}: '
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
        playlists[str(guild.id)] = Playlist(client, guild, guild_ref)

    playlist = playlists[str(guild.id)]

    await playlist.playlist_lock.acquire()

    guilds_ref = db.reference("guilds").child(f"{guild.id}")

    async def start_player():
        player = await playlist.add_to_playlist(link_or_phrase, False, message.author.name, output_channel)
        audio_source = await player.get_new_audio_source()
        playlist.now_playing = audio_source.title
        active_player = {
            "title": audio_source.title, "volume": audio_source.volume,
            "thumbnail": audio_source.data["thumbnail"], "extractor": audio_source.data["extractor"],
            "duration": audio_source.data["duration"], "url": audio_source.data["webpage_url"],
            "type": "youtube-dl", "status": "playing"
        }
        guilds_ref.update({"active_player": active_player})
        await output_channel.send(f'{message.author.name}:', embed=create_now_playing_embed(active_player))
        message.guild.voice_client.play(audio_source)

    try:
        # Must check if intro is already playing
        if server.intro_player is not None and server.intro_player.is_playing():
            # Check if there's something in the playlist
            if len(server.playlist.yt_playlist) > 0:
                player = await server.playlist.add_to_playlist(link_or_phrase, True, message.author.name, output_channel)
            else:
                await start_player()
                server.active_player.pause()

        elif server.active_player is not None and (
                not server.active_player.is_done() or server.active_player.is_playing()) \
                or len(server.playlist.yt_playlist) > 0:
            player = await server.playlist.add_to_playlist(link_or_phrase, True, message.author.name, output_channel)
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
async def repeat(message, client, db_guild, plugin):
    await message.delete()
    if server.active_player is None or not server.active_player.is_playing():
        await message.channel.send(f'{message.author.name}: Nothing to repeat!')
    else:
        await message.channel.send(f':repeat: {message.author.name} repeated {server.active_playlist_element.title}.')
        server.playlist.yt_playlist.insert(0, server.active_playlist_element)


@RegisterCommand("shuffle", "sh")
async def shuffle(message, client, db_guild, plugin):
    await message.delete()
    if server.active_player is None or not server.active_player.is_playing():
        await message.channel.send(f'{message.author.name}: Nothing to shuffle!')
    else:
        await message.channel.send(f':twisted_rightwards_arrows: {message.author.name} shuffled the list.')
        random.shuffle(server.playlist.yt_playlist)
        server.playlist.yt_playlist.sort(key=lambda element: len(element.vote_list), reverse=True)


@RegisterCommand("pause", "pa")
async def pause(message, bot_channel, client, guild_ref):
    await message.delete()
    voice_client = message.guild.voice_client
    if voice_client is None or (not voice_client.is_paused() and not voice_client.is_playing()):
        await message.channel.send(f'{message.author.name}: Nothing to pause!')
    elif voice_client.is_paused():
        await message.channel.send(f'{message.author.name}: The player is already paused!')
    else:
        await message.channel.send(f':pause_button:: {message.author.name} paused the player!')
        #server.active_playlist_element.pause_time = time.time()
        voice_client.pause()
        db.reference(f"guilds/{message.guild.id}/active_player").update({"status": "paused"})


@RegisterCommand("resume", "r")
async def resume(message, bot_channel, client, guild_ref):
    await message.delete()
    voice_client = message.guild.voice_client
    if voice_client is None or (not voice_client.is_paused() and not voice_client.is_playing()):
        await message.channel.send(f'{message.author.name}: Nothing to resume!')
    else:
        await message.channel.send(f':arrow_forward:: {message.author.name} resumed the player!')
        #server.active_playlist_element.start_time += (server.active_playlist_element.pause_time-server.active_playlist_element.start_time)
        voice_client.resume()
        db.reference(f"guilds/{message.guild.id}/active_player").update({"status": "playing"})


@RegisterCommand("volume", "sv")
async def volume(message, bot_channel, client, guild_ref):
    await message.delete()
    voice_client = message.guild.voice_client
    if voice_client is None or (not voice_client.is_paused() and not voice_client.is_playing()):
        await message.channel.send(f'{message.author.name}: Nothing is playing!')
    else:
        parameters = message.content.split()
        if len(parameters) < 2:
            current_volume = voice_client.source.volume
        else:
            try:
                current_volume = float(parameters[1])/2/100.0
            except ValueError:
                await message.channel.send(f'{message.author.name}: Please give a numeric value!')
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
            await message.channel.send(f'{icon}: {message.author.name}, '
                                       f'the volume for the current track is {int(current_volume*2*100.0)}%!')
        elif parameters[1] == current_volume:
            await message.channel.send(f'{icon}: {message.author.name}, the volume is already the given value!')
        else:
            if current_volume < 0.0:
                current_volume = 0.0
            elif current_volume > 0.5:
                current_volume = 0.5

            await message.channel.send(f'{icon}: {message.author.name}, the volume was changed from '
                                       f'{int(voice_client.source.volume*2*100.0)}% to '
                                       f'{int(current_volume*2*100.0)}%!')
            voice_client.source.volume = current_volume
            db.reference(f"guilds/{message.guild.id}/active_player").update({"volume": current_volume})


@RegisterCommand("delete", "d", "remove")
async def delete(message, client, db_guild, plugin):
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
        playlist_element = server.playlist.yt_playlist[index]
        server.playlist.yt_playlist.remove(playlist_element)
        await message.channel.send(f"{message.author.name}: Entry \'{playlist_element.title}\' "
                                   f"with index {index+1} was deleted from the queue.")
    except IndexError:
        await message.channel.send(f'{message.author.name}: Index {index+1} is out of queue bounds!')


@RegisterCommand("skip", "sk")
async def skip(message, client, db_guild, plugin):
    await message.delete()
    await server.playlist.playlist_lock.acquire()
    try:
        if server.active_player is None and len(server.playlist.yt_playlist) > 0:
            await message.channel.send(f'{message.author.name}: Nothing to skip!')
        else:
            await message.channel.send(f':track_next:: {message.author.name} skipped the song!')
            server.active_player.stop()
    finally:
        server.playlist.playlist_lock.release()


@RegisterCommand("next", "n")
async def next(message, client, db_guild, plugin):
    await message.delete()
    if len(server.playlist.yt_playlist) > 0:
        await message.channel.send(f'{message.author.name}: The next song is {server.playlist.yt_playlist[0].title}')
    else:
        await message.channel.send(f'{message.author.name}: There is no next song as the queue is empty!')

@RegisterCommand("stop", "s", "stahp", "stap")
async def stop(message, bot_channel, client, guild_ref):
    await message.delete()
    voice_client = message.guild.voice_client
    if voice_client and voice_client.is_playing() and not voice_client.is_paused():
        voice_client.stop()
        playlists[str(message.guild.id)].yt_playlist.clear()
        await message.channel.send(f':stop_button:: {message.author.name} stopped the player and cleared the queue!')
    else:
        await message.channel.send(f'{message.author.name}: No active player to stop!')
