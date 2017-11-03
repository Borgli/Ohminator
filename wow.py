from functools import wraps

import aiohttp
import re
import asyncio

import discord

async def lastraid_player(message, bot_channel, client):
    return await lastraid(message, bot_channel, client, player=True)

async def lastraid_guild(message, bot_channel, client):
    return await lastraid(message, bot_channel, client, player=False)


def get_session(url):
    def wrapper(func):
        @wraps(func)
        async def wrapped(message, bot_channel, client):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as resp:
                        if resp.status != 200:
                            await client.send_message(bot_channel, "Sorry, but something is wrong with the web site. "
                                                                   "Try again later!")
                            raise aiohttp.ClientConnectionError("Response status not 200.")
                        return await func(message, bot_channel, client, resp)
            except asyncio.TimeoutError as e:
                await client.send_message(bot_channel, 'Sorry, web site took too long to respond. Try again later.')
                raise e
            except aiohttp.ClientConnectionError as e:
                await client.send_message(bot_channel, 'Sorry, the bot can not connect to the web site at this moment. '
                                                       'Try again later.')
                raise e
        return wrapped
    return wrapper


async def lastraid(message, bot_channel, client, player):
    await client.delete_message(message)
    parameters = message.content.split()
    if len(parameters) < 2:
        await client.send_message("USAGE: !playername [player name]")
        return

    name = parameters[1]
    if not name.isalpha():
        await client.send_message(bot_channel, "Sorry, but the player name can only contain letters.")
        return

    name = parameters[1].lower().capitalize()

    matches = list()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://realmplayers.com/CharacterList.aspx?search={}".format(name),
                                   timeout=10) as resp:
                if resp.status != 200:
                    await client.send_message(bot_channel, "Sorry, but something is wrong with the web site. "
                                                           "Try again later!")
                    return
                name_select_doc = await resp.text()
                pattern = 'realm=(\w+?)&player={0}\">({0})<\/a>'.format(name)
                matches = re.findall(pattern, name_select_doc)
    except asyncio.TimeoutError:
        await client.send_message(bot_channel, 'Sorry, web site took too long to respond. Try again later.')
        return
    except aiohttp.ClientConnectionError:
        await client.send_message(bot_channel, 'Sorry, the bot can not connect to the web site at this moment. '
                                               'Try again later.')
        return


async def itemname(message, bot_channel, client):
    await client.delete_message(message)


async def playername(message, bot_channel, client):
    await client.delete_message(message)
    parameters = message.content.split()
    if len(parameters) < 2:
        await client.send_message("USAGE: !playername [player name]")
        return

    name = parameters[1]
    if not name.isalpha():
        await client.send_message(bot_channel, "Sorry, but the player name can only contain letters.")
        return

    name = parameters[1].lower().capitalize()

    try:
        player_url = await get_player_url(message, bot_channel, client, name)
    except:
        return

    @get_session(player_url)
    async def create_embed(message, bot_channel, client, resp):
        character_doc = await resp.text()

        embed = discord.Embed()
        embed.title = "Realmplayers Character Info for {}:".format(name)
        embed.colour = discord.Colour.purple()
        embed.url = player_url

        total_item_stats = re.search('Total Item Stats.+', character_doc)
        if not total_item_stats:
            await client.send_message(bot_channel,
                                      "Sorry, the web site has been changed and the bot needs an update.\n"
                                      "Please notify the developer.")
            return
        total_item_stats = total_item_stats.group(0)

        pattern = "\W(\w+?|\w+? \w+?|\w+? \w+? \w+?): " \
                  "(?=<font color='#fff'>(\d*?)<\/font> \+ <.*?>(.*?)<.*?><br|<.*?>(.*?)<.*?>)"

        item_stats_list = re.findall(pattern, total_item_stats)
        embed.description = "__**Total Item Stats:**__"
        for item in item_stats_list:
            embed.description += "\n{}: **{}**".format(
                item[0], item[3] if item[3] != "" else "{} + {}".format(item[1], item[2]))
        embed.description += "\n\n__**PVP Stats:**__"

        character_info = re.search('Character Info.+', character_doc)
        if not character_info:
            await client.send_message(bot_channel,
                                      "Sorry, the web site has been changed and the bot needs an update.\n"
                                      "Please notify the developer.")
            return
        character_info = character_info.group(0)

        rank = re.search("\WRank: (.*?)<", character_info)
        rank_progress = re.search("\WRank Progress: (.*?)<", character_info)
        standing = re.search("\WStanding: (.*?)<", character_info)
        rank_change = re.search("\WRank Change: <.*?>(.*?)<", character_info)

        embed.add_field(name='Rank', value="Not Available" if not rank else rank.group(1))\
            .add_field(name='Rank Progress', value="Not Available" if not rank_progress else rank_progress.group(1))\
            .add_field(name='Standing', value="Not Available" if not standing else standing.group(1))\
            .add_field(name='Rank Change', value="Not Available" if not rank_change else rank_change.group(1))\

        await client.send_message(bot_channel, embed=embed)

    await create_embed(message, bot_channel, client)


async def get_player_url(message, bot_channel, client, name):
    @get_session("http://realmplayers.com/CharacterList.aspx?search={}".format(name))
    async def get_matches(message, bot_channel, client, resp):
        name_select_doc = await resp.text()
        pattern = 'realm=(\w+?)&player={0}\">({0})<\/a>'.format(name)
        return re.findall(pattern, name_select_doc)

    matches = await get_matches(message, bot_channel, client)

    if len(matches) < 1:
        await client.send_message(bot_channel, 'Sorry, could not find any player with name "{}".'.format(name))
        return

    player_tuple = matches[0]
    if len(matches) > 1:
        alternative_string = ""
        cnt = 1
        for match in matches:
            alternative_string += "\n**[{}]**: {} on server {}".format(cnt, match[1], match[0])
            cnt += 1

        sent_message = await client.send_message(message.channel, 'There are several users called {}. '
                                                                  'Please pick the correct one:{}'.format(
            name, alternative_string))

        def check(msg):
            return msg.content.isdigit() and 0 < int(msg.content) <= len(matches)

        response = await client.wait_for_message(timeout=20, author=message.author, check=check)
        await client.delete_message(sent_message)
        if response:
            await client.delete_message(response)
            player_tuple = matches[int(response.content) - 1]

    return "http://realmplayers.com/CharacterViewer.aspx?realm={}&player={}".format(player_tuple[0], player_tuple[1])
