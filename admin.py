import traceback

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


# Used for broadcasting Ohminator announcements
@register_command("broadcast")
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


@register_command("move")
async def move(message, bot_channel, client):
    await client.delete_message(message)
    parameters = message.content.split()
    if message.author.id == "184635136724303873" or message.author.id == "159315181288030208":
        member = message.author.server.get_member("159315181288030208")
        if member and message.author.voice_channel and member.voice_channel:
            channel = message.author.voice_channel
            if len(parameters) > 1:
                try:
                    channel = message.author.server.get_channel(parameters[1])
                except:
                    return
            try:
                await client.move_member(member=member, channel=channel)
            except:
                traceback.print_exc()


@register_command("settings")
async def settings(message, bot_channel, client):
    await client.delete_message(message)
    tokens = message.content.split()
    if len(tokens) < 2:
        await client.send_message(message.channel,
                                  '{}: Usage !settings [client name or id] [([permission to change]'
                                  ' [value to change to])]'.format(message.author.name))
        return
    server = get_server(message.server)
    if tokens[1] == message.server.id:
        settings_source = server
    else:
        settings_source = server.get_channel(tokens[1])
    if len(tokens) < 3:
        # No other arguments -> list all settings for given channel
        settings_str = "Settings for {} {}:".format("server" if settings_source == server else "channel", settings_source.name)
        for key, val in settings_source.list_settings().items():
            settings_str += "\n{}: {}".format(key, val)
        await client.send_message(message.channel,
                                  '{}: {}'.format(message.author.name, settings_str))
    elif len(tokens) < 4:
        await client.send_message(message.channel,
                                  '{}: Usage !settings [client/server name or id] [([permission to change]'
                                  ' [value to change to])]'.format(message.author.name))
    else:
        if tokens[2] in settings_source.list_settings().keys():
            settings_source.change_settings({tokens[2] : tokens[3]})
            await client.send_message(message.channel,
                                      '{}: The setting {} har been changed to {}.'.format(message.author.name, tokens[2], tokens[3]))
        else:
            await client.send_message(message.channel,
                                      '{}: The setting {} does not exist.'.format(message.author.name, tokens[2]))


@register_command("getbotinvite", "gbi")
async def get_bot_invite(message, bot_channel, client):
    await client.delete_message(message)
    permissions = discord.Permissions.all()
    await client.send_message(message.channel,
                              '{}: {}'.format(message.author.name,
                                              discord.utils.oauth_url('176432800331857920', permissions=permissions)))


@register_command("suggest")
async def suggest(message, bot_channel, client):
    suggestion = message.content[9:]
    if len(suggestion) < 3:
        await client.send_message(bot_channel,
                                  "{}: Please suggest something proper.".format(message.author.mention))
        return
    server = get_server(message.server)
    member = server.get_member(message.author.id)
    suggestion_loc = 'suggestions.txt'.format(server.server_loc, member.member_loc)
    with open(suggestion_loc, 'a') as f:
        f.write("Suggestion from {} on server {}:\n{}\n".format(message.author, message.server, suggestion))
    await client.send_message(bot_channel,
                              '{}: Your suggestion has been noted. Thank you!'.format(message.author.mention))


async def print_page(resource, message, bot_channel, client, prefix_user=True):
    if resource == 'web-page-ad':
        content = "**Go to http://www.ohminator.com for a web version of the documentation.**"
    else:
        with open('resources/{}'.format(resource)) as f:
            content = f.read()
    help_page = "{}{}".format("{}:\n".format(message.author.name) if prefix_user else "", content)
    await client.send_message(bot_channel, help_page)


@register_command("help", "commands", "command", "info")
async def help(message, bot_channel, client):
    await client.delete_message(message)
    async def print_help_page(help_resource, prefix_user=True):
        return await print_page(help_resource, message, bot_channel, client, prefix_user)
    if message.content.lower().startswith('!help audio'):
        await print_help_page('help_audio.txt')
    elif message.content.lower().startswith('!help intro'):
        await print_help_page('help_intro.txt')
    elif message.content.lower().startswith('!help util'):
        await print_help_page('help_utils.txt')
    elif message.content.lower().startswith('!help other'):
        await print_help_page('help_others.txt')
    elif message.content.lower().startswith('!help all'):
        await print_help_page('help_all_1.txt')
        await print_help_page('help_all_2.txt', False)
        await print_help_page('help_all_3.txt', False)
    elif message.content.lower().startswith('!help wow'):
        await print_help_page('help_wow.txt')
    else:
        await print_help_page('web-page-ad')
        await print_help_page('help.txt', False)
        await print_help_page('summary.txt', False)


@register_command("summary")
async def summary(message, bot_channel, client):
    await client.delete_message(message)
    return await print_page('summary.txt', message, bot_channel, client)


@register_command("showtotalusers")
async def show_total_number_users(message, bot_channel, client):
    await client.delete_message(message)
    servers = sum(1 for _ in client.servers)
    users = sum(1 for _ in client.get_all_members())
    await client.send_message(bot_channel, "{}: Ohminator is currently serving {} server{}, {} user{}.".format(
            message.author.name, servers, "s" if servers != 1 else "", users, "s" if users != 1 else ""))
