import discord

server_list = list()


def get_server(discord_server):
    for server in server_list:
        if server.id == discord_server.id:
            return server


def get_bot_channel(message_server):
    if message_server is None:
        return None
    return get_server(message_server).bot_channel


def create_now_playing_embed(now_playing):
    embed = discord.Embed()
    embed.title = "Now playing:"
    embed.colour = discord.Colour.dark_green()
    embed.description = "[{}]({})\n{}".format(now_playing.title, now_playing.webpage_url,
                                              'It is {} seconds long'.format(now_playing.duration))
    low_res_thumbnail = now_playing.thumbnail
    url_splitted = low_res_thumbnail.split('/')
    url_splitted[-1] = 'mqdefault.jpg'
    high_res_thumbnail = '/'.join(url_splitted)
    embed.set_thumbnail(url=high_res_thumbnail)
    return embed


class NoChannelFoundError(BaseException):
    pass

class NoMemberFoundError(BaseException):
    pass
