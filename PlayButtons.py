import traceback

class PlayButtons:
    def __init__(self, play, pause, stop, next_track, volume_up, volume_down, queue):
        self.play = play
        self.pause = pause
        self.stop = stop
        self.next_track = next_track
        self.volume_up = volume_up
        self.volume_down = volume_down
        self.queue = queue

    async def handle_message(self, message, server, client):
        if server.active_player is None:
            return
        try:
            if message.id == self.play.id:
                server.active_player.resume()
            elif message.id == self.pause.id:
                server.active_player.pause()
            elif message.id == self.stop.id:
                server.playlist.yt_playlist.clear()
                server.active_player.stop()
            elif message.id == self.next_track.id:
                server.active_player.stop()
            elif message.id == self.queue.id:
                cnt = 1
                queue = str()
                more_entries = False
                for play in server.playlist.yt_playlist:
                    if cnt <= 30:
                        queue += "{}: {}\n".format(cnt, play.title)
                    else:
                        more_entries = True
                    cnt += 1
                if more_entries is True:
                    if cnt - 30 == 1:
                        entry = 'entry'
                    else:
                        entry = 'entries'
                    queue += "And {} {} more...".format(cnt - 30, entry)
                await client.send_message(server.bot_channel,
                                          'Here is the current queue:\n{}'.format(queue.strip()))
            elif message.id == self.volume_up.id:
                if not server.active_player.volume > 1.8:
                    server.active_player.volume += 0.2
            elif message.id == self.volume_down.id:
                if not server.active_player.volume < 0.2:
                    server.active_player.volume -= 0.2
        except:
            traceback.print_exc()
