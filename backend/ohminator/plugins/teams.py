import random

from utils import *


async def join(message, bot_channel, client):
    await client.delete_message(message)
    server = get_server(message.server)
    if message.author not in server.split_list:
        server.split_list.append(message.author)
        await client.send_message(bot_channel,
                                  '{}: You have joined the queue!\n'
                                  'Current queue: {}'.format(message.author.mention, server.print_queue()))
    else:
        await client.send_message(bot_channel, '{}: You are already in the queue!'.format(message.author.mention))

async def leave(message, bot_channel, client):
    await client.delete_message(message)
    server = get_server(message.server)
    if message.author in server.split_list:
        server.split_list.remove(message.author)
        await client.send_message(bot_channel,
                                  '{}: You have left the queue!\n'
                                  'Current queue: {}'.format(message.author.mention, server.print_queue()))
    else:
        await client.send_message(bot_channel, '{}: You are not in the queue!'.format(message.author.mention))

async def team_queue(message, bot_channel, client):
    await client.delete_message(message)
    server = get_server(message.server)
    await client.send_message(bot_channel, '{}: Current queue: {}'.format(message.author.mention, server.print_queue()))

async def team_clear_queue(message, bot_channel, client):
    await client.delete_message(message)
    server = get_server(message.server)
    server.split_list.clear()
    await client.send_message(bot_channel, '{}: The team queue has been cleared.'.format(message.author.name))


@register_command("team")
async def team(message, bot_channel, client):
    subcommands = {
        "join": join,
        "leave": leave,
        "queue": team_queue,
        "clear": team_clear_queue
    }
    parameters = message.content.lower().split()
    # Check if there are subcommands.
    if len(parameters) > 1:
        if parameters[1] in subcommands:
            await subcommands[parameters[1]](message, bot_channel, client)


@register_command("split")
async def split(message, bot_channel, client):
    await client.delete_message(message)
    try:
        num_teams = int(message.content.split()[1])
    except:
        await client.send_message(bot_channel,
                                  '{}: Invalid parameter for !split. Use number of teams!'.format(message.author.name))
        return

    channel_list = list()
    for team_number in range(num_teams):
        channel = discord.utils.get(message.author.server.channels, name='Team {}'.format(team_number + 1))
        if channel is None:
            channel_list.append(
                await client.create_channel(message.author.server, 'Team {}'.format(team_number + 1),
                                            type=discord.ChannelType.voice))
        else:
            channel_list.append(channel)

    server = get_server(message.server)
    division = len(server.split_list) / float(num_teams)
    random.shuffle(server.split_list)
    teams = [server.split_list[int(round(division * i)): int(round(division * (i + 1)))] for i in range(num_teams)]

    index = 0
    for team in teams:
        for member in team:
            await client.move_member(member, channel_list[index])
        index += 1


@register_command("removeteams")
async def removeteams(message, bot_channel, client):
    await client.delete_message(message)
    team_number = 1
    while True:
        channel = discord.utils.get(message.author.server.channels, name='Team {}'.format(team_number))
        if channel is None:
            break
        else:
            await client.delete_channel(channel)
        team_number += 1
