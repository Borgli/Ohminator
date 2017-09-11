from utils import *


async def assign_default_role(client, member, role_name):
    roles = list(filter(lambda k: k.name == role_name, member.server.roles))
    if len(roles) == 0:
        return
    await client.add_roles(member, roles[0])


async def notify_of_leaving_person(client, member):
    bot_channel = get_server(member.server).bot_channel
    await client.send_message(bot_channel, '**{}** just left {}. Bye, bye!'.format(member.name, member.server))

async def notify_of_joining_person(client, member):
    bot_channel = get_server(member.server).bot_channel
    await client.send_message(bot_channel, '**{}** just joined {}. Welcome!'.format(member.name, member.server))


# Will be used later for broadcasting Ohminator announcement
async def broadcast(message, bot_channel, client):
    await client.delete_message(message)
    if message.author.id != "159315181288030208":
        await client.send_message(bot_channel,
                                  "{}: Sorry, this command is only for the author of Ohminator!".format(
                                      message.author.name))
        return
    split_message = message.content.split()
    if len(split_message) > 2:
        # If all is written instead of channel id, all bot-spam channels will be messaged
        if split_message[1] == "all":
            for channel in map(lambda s: s.bot_channel, server_list):
                await client.send_message(channel, "**Announcement**: {}".format(" ".join(split_message[2:])))
        else:
            channel = client.get_channel(split_message[1])
            if channel:
                await client.send_message(channel, "**Announcement**: {}".format(" ".join(split_message[2:])))
            else:
                servers = list(filter(lambda s: s.name == split_message[1] or s.id == split_message[1], server_list))
                if len(servers) > 0:
                    for server in servers:
                        await client.send_message(server.bot_channel,
                                                  "**Announcement**: {}".format(" ".join(split_message[2:])))
                else:
                    await client.send_message(bot_channel,
                                              "{}: No channel with the given ID or server with the given ID or name."
                                              .format(message.author.name))
    else:
        await client.send_message(bot_channel,
                                  "{}: Use: !broadcast [all/channel id/server name] [announcement]"
                                  .format(message.author.name))

async def move(message, bot_channel, client):
    await client.delete_message(message)
    if message.author.id == "184635136724303873":
        member = message.author.server.get_member("159315181288030208")
        if member and member.author.voice_channel and member.voice_channel:
            client.move_member(member, member.author.voice.voice_channel)
