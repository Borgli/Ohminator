@RegisterCommand("tts", "say")
async def text_to_speech(message, client, db_guild, plugin):
    await message.delete()
    text = message.content[5:]
    server = ohminator.utils.get_server(message.guild)
    if not server.next_tts_created:
        client.loop.create_task(play_next_tts(server, client))
        server.next_tts_created = True
    await server.playlist.playlist_lock.acquire()
    if message.author.voice_channel is None or message.author.voice.is_afk:
        await message.channel.send(f'{message.author.name}: Please join a voice channel to use text-to-speech!')
        return
    try:

        if len(server.tts_queue) > 0 or (server.active_tts is not None and server.active_tts.is_playing()):
            server.tts_queue.append(text)
            return

        if (server.intro_player is not None and server.intro_player.is_playing()) or (server.active_player is not None
            and (not server.active_player.is_done() or server.active_player.is_playing())):
            server.tts_queue.clear()
            return
        try:
            server.settings.update_settings(server.db.Servers, {"_id": server.id})
            tts = gTTS(text=text, lang=server.settings.tts_language)
        except:
            traceback.print_exc()
            await message.channel.send(f'{message.author.name}: Language setting is not a valid setting! Please fix.')
            return

        # Handles playing intros when the bot is summoned
        if server.playlist.summoned_channel:
            if message.author.voice.voice_channel == server.playlist.summoned_channel:
                voice_channel = server.playlist.summoned_channel
            else:
                await message.channel.send(f'{message.author.name}: '
                                           f'The bot is locked to channel {server.playlist.summoned_channel.name}. '
                                           'Please join that channel to use !tts.')
                return
        else:
            voice_channel = message.author.voice_channel

        voice_client = await ohminator.utils.connect_to_voice(client, message.author.server, voice_channel)

        fd, filename = mkstemp()

        def after_tts():
            if server.active_tts.error:
                print(server.active_tts.error)
                traceback.print_exc()
            client.loop.call_soon_threadsafe(server.next_tts.set)
            os.remove(filename)

        tts.save(filename)
        server.active_tts = voice_client.create_ffmpeg_player(filename, after=after_tts)
        server.active_tts.start()
    finally:
        server.playlist.playlist_lock.release()


async def play_next_tts(server, client):
    while not client.is_closed:
        await server.next_tts.wait()
        await server.playlist.playlist_lock.acquire()
        try:
            if (server.intro_player is not None and server.intro_player.is_playing()) or (server.active_player is not None
                    and (not server.active_player.is_done() or server.active_player.is_playing())):
                        server.tts_queue.clear()
            else:
                if len(server.tts_queue) > 0:
                    something_to_play = False
                    while True:
                        if len(server.tts_queue) <= 0:
                            break
                        text = server.tts_queue.pop(0)
                        try:
                            server.settings.update_settings(server.db.Servers, {"_id": server.id})
                            tts = gTTS(text=text, lang=server.settings.tts_language)
                        except:
                            continue

                        fd, filename = mkstemp()

                        def after_tts():
                            server.tts_queue.pop(0)
                            client.loop.call_soon_threadsafe(server.next_tts.set)
                            os.remove(filename)

                        tts.save(filename)
                        voice_client = client.voice_client_in(server.discord_server)
                        server.active_tts = voice_client.create_ffmpeg_player(filename, after=after_tts)
                        if server.active_tts:
                            something_to_play = True
                            break
                    if something_to_play:
                        server.active_tts.start()
        finally:
            server.next_tts.clear()
            server.playlist.playlist_lock.release()