server_list = list()


def get_server(discord_server):
    for server in server_list:
        if server.id == discord_server.id:
            return server


def get_bot_channel(message_server):
    if message_server is None:
        return None
    return get_server(message_server).bot_channel
