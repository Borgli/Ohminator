from utils import *


async def assign_default_role(client, member, role_name):
    roles = list(filter(lambda k: k.name == role_name, member.server.roles))
    if len(roles) == 0:
        return
    await client.add_roles(member, roles[0])


async def notify_of_leaving_person(client, member):
    bot_channel = get_server(member.server).bot_channel
    await client.send_message(bot_channel, '{} just left {}. Bye, bye!'.format(member.name, member.server))

async def notify_of_joining_person(client, member):
    bot_channel = get_server(member.server).bot_channel
    await client.send_message(bot_channel, '{} just joined {}. Welcome!'.format(member.name, member.server))


# Will be used later for broadcasting Ohminator announcement
async def broadcast(message, bot_channel, client):
    await client.delete_message(message)
    split_message = message.content.split()
    if len(split_message) > 2:
        # If all is written instead of channel id, all bot-spam channels will be messaged
        if split_message[1] == "all":
            for channel in map(lambda s: s.bot_channel, server_list):
                await client.send_message(channel, "**Console**: {}".format(" ".join(split_message[2:])))
        else:
            channel_id = split_message[1]
            channel = client.get_channel(channel_id)
            if channel:
                await client.send_message(channel, "**Console**: {}".format(" ".join(split_message[2:])))
            else:
                await client.send_message(bot_channel, "No channel with the given ID.")
