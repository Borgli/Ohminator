import discord
import asyncio
import time
import random

client = discord.Client()

class Ohminator:
    current_voice = None
    active_player = None
    intro_names = {'runarl', 'Rune', 'Chimeric', 'Johngel', 'Christian Berseth',
                   'Jan Ivar Ugelstad', 'Christian F. Vegard', 'Martin', 'Kristoffer Skau', 'Ginker', 'aekped',
                                                                                                      'sondrehav'}
    black_list = {'Christian Berseth', 'Chimeric'}
    yt_lock = asyncio.Lock(loop=client.loop)
    time_alive = time.time()

    help_message = '{}: List of commands: \n' \
                   '!help or !command\t-\tPrints out this menu.\n ' \
                   '!yt [youtube link]\t\t-\tPlays audio from YouTube in voice channel of caller.\n ' \
                   '!stahp\t\t\t\t\t\t-\tStops any playing sound.\n' \
                   '!joined\t\t\t\t\t\t-\tTells you when you joined Ohm!\n' \
                   '!roll [lowest] [highest]\t\t\t\t\t-\tRoll a number between lowest and highest.\n' \
                   '!intro\t\t\t\t\t\t-\t Plays your intro.\n'

ohm = Ohminator()


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

async def move_to_voice_channel(user):
    # Check where the bot is currently and move it as necessary
    if client.is_voice_connected(user.server):
        voice_client = client.voice_client_in(user.server)
        # If the bot is connected to the same one as the author we don't need to change it.
        if voice_client == user.voice_channel:
            ohm.current_voice = voice_client
        else:
            await voice_client.disconnect()
            ohm.current_voice = await client.join_voice_channel(user.voice_channel)
    else:
        ohm.current_voice = await client.join_voice_channel(user.voice_channel)


async def play_intro(name):
    try:
        ohm.active_player = ohm.current_voice.create_ffmpeg_player('{}/intro.wav'.format(name))
        ohm.active_player.start()
    except Exception as e:
        print(e)

async def play_yt(message):
    link = message.content[4:]
    await client.delete_message(message)

    # Check whether author is afk or not
    if message.author.is_afk:
        return

    # Check if author is in a voice channel or not.
    # The link will not be played if the author is not in a voice channel.
    if message.author.voice_channel is None:
        await client.send_message(message.channel,
                                  '{}: Please join a voice channel to play your link!'.format(message.author.name))
        return

    # Check whether something is already playing or not
    if ohm.active_player is not None and ohm.active_player.is_playing():
        await client.send_message(message.channel, '{}: Something is already playing!'.format(message.author.name))
        return

    await move_to_voice_channel(message.author)

    try:
        ohm.active_player = await ohm.current_voice.create_ytdl_player(link)
        await client.send_message(message.channel,
                                  '{}: \nNow playing: {}\nIt is {} seconds long'.format(
                                      message.author.name, ohm.active_player.title, ohm.active_player.duration))
        ohm.active_player.start()
    except:
        await client.send_message(message.channel, '{}: Your link could not be played!'.format(message.author.name))

async def stop_current_playing(message):
    await client.delete_message(message)
    if ohm.active_player is None or not ohm.active_player.is_playing:
        await client.send_message(message.channel, '{}: No active player!'.format(message.author.name))
    else:
        await client.send_message(message.channel, '{} stopped the player!'.format(message.author.name))
        ohm.active_player.stop()

async def play_intro_from_message(message):
    if message.author.voice_channel is None or message.author.is_afk:
        await client.send_message(message.channel,
                                  '{}: Please join a voice channel to play your link!'.format(message.author.name))
        return

    # Check if the name is in the list of intros and plays it.
    if message.author.name is not None and message.author.name in ohm.intro_names:
        await move_to_voice_channel(message.author)

        if ohm.active_player is not None and ohm.active_player.is_playing():
            ohm.active_player.stop()
        await play_intro(message.author.name)

@client.event
async def on_message(message):

    if message.content.startswith('!yt'):
        await play_yt(message)

    elif message.content.startswith('!stahp') or message.content.startswith('!stop'):
        await stop_current_playing(message)

    elif message.content.startswith('!intro'):
        await client.delete_message(message)
        await play_intro_from_message(message)

    elif message.content.startswith('!member'):
        await client.delete_message(message)
        await client.send_message(message.channel,
                                  'Not a member yet?'
                                  '\nBecome a member today for a limited time offer of 5$/month.'
                                  '\nEnjoy perks as unlimited YouTube plays, '
                                  'YouTube priority and access to the !spam command!')

    elif message.content.startswith('!spam'):
        await client.delete_message(message)
        await client.send_message(message.channel,
                                  '{}: Please pay 5$ to unlock the !spam command.'.format(message.author.name))

    elif message.content.startswith('!ohmage'):
        await client.delete_message(message)
        await client.send_message(message.channel, '{}: Ohm was created {}!'.format(message.author.name,
                                                                                    message.server.created_at))

    elif message.content.startswith('fuck'):
        await client.send_message(message.channel, 'No, fuck you, {}!'.format(message.author.name))

    elif message.content.startswith('!help') or message.content.startswith('!commands'):
        await client.delete_message(message)
        await client.send_message(message.channel, ohm.help_message.format(message.author.name))

    elif message.content.startswith('!ohminator'):
        await client.delete_message(message)
        await client.send_message(message.channel, 'I am the Ohminator, bleep, bloop! Type !help to see a list of '
                                                   'commands!')

    elif message.content.startswith('!roll'):
        try:
            options = message.content.split()
            rand = random.randint(int(options[1]), int(options[2]))
            await client.send_message(message.channel, '{}: You rolled {}!'.format(message.author.name, rand))
        except:
            await client.send_message(message.channel,
                                      '{}: Could not roll with those parameters!'.format(message.author.name))

    elif message.content.startswith('!joined'):
        await client.delete_message(message)
        await client.send_message(message.channel, '{}: You joined the Ohm server {}!'.format(message.author.name,
                                                                                              message.author.joined_at))

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

        await move_to_voice_channel(after)

        if ohm.active_player is not None and ohm.active_player.is_playing():
            ohm.active_player.stop()

        await play_intro(before.name)

client.run('MTc2NDMzMTMwMzM1NTAyMzM3.CgvoFg.FLaupAZZ5OviZ1Fb7gAO_Aq-sLo')