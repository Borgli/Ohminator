from utils import *


async def assign_default_role(client, member, role_name):
    await client.add_roles(member, filter(lambda k: k.name == role_name, member.server.roles))


async def notify_of_leaving_person(client, member):
    bot_channel = get_server(member.server).bot_channel
    await client.send_message(bot_channel, '{} just left {}. Bye, bye!'.format(member.name, member.server))

async def notify_of_joining_person(client, member):
    bot_channel = get_server(member.server).bot_channel
    await client.send_message(bot_channel, '{} just joined {}. Welcome!'.format(member.name, member.server))