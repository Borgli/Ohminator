import discord
import asyncio


class Ohminator:
    current_voice = None
    active_player = None
    intro_names = {'runarl', 'Rune', 'Chimeric', 'Johngel'}

class Stats:
    time_spent_total = None


client = discord.Client()
ohm = Ohminator()


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


@client.event
async def on_message(message):
    """if message.content.startswith('!test'):
        counter = 0
        tmp = await client.send_message(message.channel, 'Calculating messages...')
        async for log in client.logs_from(message.channel, limit=100):
            if log.author == message.author:
                counter += 1

        await client.edit_message(tmp, 'You have {} messages.'.format(counter))
    elif message.content.startswith('!sleep'):
        await asyncio.sleep(5)
        await client.send_message(message.channel, 'Done sleeping')
    """
    if message.content.startswith('!yt'):
        link = message.content[4:]
        if ohm.current_voice is None:
            ohm.current_voice = await client.join_voice_channel(message.author.voice_channel)
        elif ohm.current_voice.channel != message.author.voice_channel:
            await ohm.current_voice.disconnect()
            ohm.current_voice = await client.join_voice_channel(message.author.voice_channel)

        await client.delete_message(message)
        if ohm.active_player is not None and ohm.active_player.is_playing():
            await client.send_message(message.channel, 'Something is already playing!')
            return

        try:
            ohm.active_player = await ohm.current_voice.create_ytdl_player(link)
            ohm.active_player.start()
        except:
            await client.send_message(message.channel, '{}: Your link could not be played!'.format(message.author.name))

    elif message.content.startswith('!stahp') or message.content.startswith('!stop'):
        await client.delete_message(message)
        if ohm.active_player is None or not ohm.active_player.is_playing:
            await client.send_message(message.channel, 'No active player!')
        else:
            ohm.active_player.stop()

    elif message.content.startswith('!help') or message.content.startswith('!commands'):
        await client.delete_message(message)
        await client.send_message(message.channel,
                                  'List of commands: \n'
                                  '!help or !command\t-\tPrints out this menu.\n'
                                  '!yt [youtube link]\t\t-\tPlays audio from YouTube in voice channel of caller.\n'
                                  '!stahp\t\t\t\t\t\t-\tStops any playing sound.\n')

    elif message.content.startswith('!ohminator'):
        await client.delete_message(message)
        await client.send_message(message.channel, 'I am the Ohminator, bleep, bloop! Type !help to see a list of '
                                                   'commands!')

    elif message.content.startswith('!roll'):
        pass



@client.event
async def on_voice_state_update(before, after):
    if before.name is not None and before.name in ohm.intro_names \
            and before.voice_channel != after.voice_channel:

        if ohm.current_voice is None:
            ohm.current_voice = await client.join_voice_channel(after.voice_channel)

        elif ohm.current_voice.channel != after.voice_channel:
            await ohm.current_voice.disconnect()

            if after.voice_channel is not None:
                try:
                    ohm.current_voice = await client.join_voice_channel(after.voice_channel)
                except:
                    return
                """
                if not client.is_voice_connected(after.voice_channel.server):
                    try:
                        ohm.current_voice = await client.join_voice_channel(after.voice_channel)
                    except discord.errors.ConnectionClosed:
                        client.connect()
                        ohm.current_voice = await client.join_voice_channel(after.voice_channel)
                """
            else:
                return
        else:
            return

        if ohm.active_player is not None and ohm.active_player.is_playing():
            ohm.active_player.stop()

        try:
            if before.name == 'runarl':
                ohm.active_player = ohm.current_voice.create_ffmpeg_player('InnspillingRunar.m4a')
            elif before.name == 'Johngel':
                ohm.active_player = ohm.current_voice.create_ffmpeg_player('Christer.wav')
            elif before.name == 'Chimeric':
                ohm.active_player = ohm.current_voice.create_ffmpeg_player('MariusJingle.wav')
            else:
                ohm.active_player = ohm.current_voice.create_ffmpeg_player('Runejingle2.wav')
            ohm.active_player.start()
        except Exception as e:
            print(e)

#stats_file = open('ohmstats', 'wb+')


client.run('MTc2NDMzMTMwMzM1NTAyMzM3.CgvoFg.FLaupAZZ5OviZ1Fb7gAO_Aq-sLo')
