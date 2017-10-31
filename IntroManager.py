import asyncio


class IntroManager:
    def __init__(self, client, ohm_server):
        self.client = client
        self.ohm_server = ohm_server
        self.intro_counter = 0
        self.intro_finished = asyncio.Event()
        self.intro_counter_lock = asyncio.Lock()
        client.loop.create_task(self.resume_playing_sound())

    async def resume_playing_sound(self):
        while not self.client.is_closed:
            await self.intro_finished.wait()
            await self.intro_counter_lock.acquire()
            try:
                self.intro_counter -= 1
                if self.intro_counter == 0:
                    if self.ohm_server.active_player is not None:
                        self.ohm_server.active_player.resume()
            finally:
                self.intro_counter_lock.release()
                self.intro_finished.clear()

    def after_intro(self):
        self.client.loop.call_soon_threadsafe(self.intro_finished.set)
        #print("Intro finished playing.")
