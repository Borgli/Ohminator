from functools import wraps

import aiohttp
import re
import asyncio
import ast

from utils import *

import discord


def wow_lock():
    def wrapper(func):
        @wraps(func)
        async def wrapped(message, bot_channel, client):
            server = utils.get_server(message.server)
            try:
                await server.wow_lock.acquire()
                return await func(message, bot_channel, client)
            finally:
                server.wow_lock.release()
        return wrapped
    return wrapper


@wow_lock()
@register_command("lastraid", "raidplayer")
async def lastraid_player(message, bot_channel, client):
    return await lastraid(message, bot_channel, client, player=True)


@wow_lock()
@register_command("raidguild")
async def lastraid_guild(message, bot_channel, client):
    return await lastraid(message, bot_channel, client, player=False)


def get_session(url):
    def wrapper(func):
        @wraps(func)
        async def wrapped(message, bot_channel, client):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=20) as resp:
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
        await client.send_message(bot_channel, "USAGE: !lastraidplayer [player name] or !lastraidguild [guild name]")
        return

    name = " ".join(parameters[1:])
    if not name.isalpha():
        await client.send_message(bot_channel, "Sorry, but the {} name can only contain letters.".format("player" if player else "guild"))
        return

    name = name.lower().capitalize()
    if player:
        try:
            player_url, player_info = await get_player_url(message, bot_channel, client, name)
        except:
            return

        player_overview_url = "http://realmplayers.com/RaidStats/PlayerOverview.aspx?realm={}&player={}".format(
            player_info[0], player_info[1])

        # Get raid stats url from the player
        @get_session(player_overview_url)
        async def get_raid_url(message, bot_channel, client, resp):
            player_doc = await resp.text()
            pattern = '<h2>Attended raids</h2><a href=\"(.+?)\">'
            return re.search(pattern, player_doc)

        try:
            match = await get_raid_url(message, bot_channel, client)
        except:
            return

        if match:
            # Get character info to find out if horde or alliance
            @get_session(player_url)
            async def get_player_doc(message, bot_channel, client, resp):
                return await resp.text()

            try:
                player_doc = await get_player_doc(message, bot_channel, client)
            except:
                return

            is_alliance = re.search('alliance_bg', player_doc)
            if is_alliance:
                player_race_icon = race_icons["alliance"]
            else:
                player_race_icon = race_icons["horde"]

            server = re.search("<span class='divider'>/</span>(.+?)</li>", player_doc)
            if not server:
                await client.send_message(bot_channel,
                                          "Sorry, the web site has been changed and the bot needs an update.\n"
                                          "Please notify the developer.")
                return

            raid_stats = "http://realmplayers.com/RaidStats/{}"

            # Get raid info to get full title and time
            @get_session(raid_stats.format(match.group(1)))
            async def get_raid_doc(message, bot_channel, client, resp):
                return await resp.text()

            try:
                raid_doc = await get_raid_doc(message, bot_channel, client)
            except:
                return

            raid_info = re.search("<a href='(RaidList\.aspx\?Guild=.+?&realm=.+?)'>(.+?)</a></li>"
                                  "<li class='active'><span class='divider'>/</span>(.+?)</li>", raid_doc)
            times = re.search("between (\d{4}(?:-\d{1,2}){2} (?:\d{2}:){2}\d{2}) and "
                              "(\d{4}(?:-\d{1,2}){2} (?:\d{2}:){2}\d{2})", raid_doc)
            if not raid_info or not times:
                await client.send_message(bot_channel,
                                          "Sorry, the web site has been changed and the bot needs an update.\n"
                                          "Please notify the developer.")
                return

            embed = discord.Embed()
            embed.set_author(name=raid_info.group(2), url=raid_stats.format(raid_info.group(1)),
                             icon_url=player_race_icon)
            embed.set_thumbnail(url=raid_icons[re.sub("\(.+?\)", '', raid_info.group(3))])
            embed.colour = discord.Colour.dark_blue()
            embed.title = raid_info.group(3).strip(" ")
            embed.url = raid_stats.format(match.group(1))
            embed.description = "Last recorded raid for **[{}]({})**\n".format(player_info[1], player_url)
            embed.description += "On server {}".format(server.group(1).strip(" "))
            embed.add_field(name="Start", value=times.group(1)).add_field(name="End", value=times.group(2))
            await client.send_message(bot_channel, embed=embed)
        else:
            await client.send_message(bot_channel, "The given player doesn't seem to have any raids on record.")

    else:
        # Get guild url from searching after the guild
        @get_session("http://realmplayers.com/CharacterList.aspx?search={}".format(name))
        async def get_guild_url(message, bot_channel, client, resp):
            search_doc = await resp.text()
            pattern = 'realm=(\w+?)&guild=({})\">&lt;.+?&gt;<\/a></td><td>.*?</td><td>.*?</td><td>.*?</td><td>.*?</td><td>(.+?)</td>'.format(name)
            return re.findall(pattern, search_doc)

        try:
            matches = await get_guild_url(message, bot_channel, client)
        except:
            return

        if len(matches) < 1:
            await client.send_message(bot_channel, 'Sorry, could not find any guild with name "{}".'.format(name))
            return

        guild_tuple = matches[0]
        response = await prompt_user(message, bot_channel, client, name, matches)
        if response:
            await client.delete_message(response)
            guild_tuple = matches[int(response.content) - 1]

        raid_link = "http://realmplayers.com/RaidStats/RaidList.aspx?realm={}&guild={}".format(guild_tuple[0], guild_tuple[1])

        # Get raid link
        @get_session(raid_link)
        async def get_last_raid_url(message, bot_channel, client, resp):
            search_doc = await resp.text()
            pattern = '<a href="(.+?)"><img src="(.+?)"\/>(.+?)<\/a><\/td><td><a href="(.+?)">' \
                      '<img src="(.+?)"\/>(.+?)<\/a><\/td><td>(.+?)<\/td><td>(.+?)<\/td><td>(.+?)<\/td><\/tr>'
            return re.search(pattern, search_doc)

        try:
            match = await get_last_raid_url(message, bot_channel, client)
        except:
            return

        if match:
            embed = discord.Embed()
            raid_stats = "http://realmplayers.com/RaidStats/{}"
            embed.set_author(name=match.group(3), url=raid_stats.format(match.group(1)), icon_url=raid_stats.format(match.group(2)))
            embed.set_thumbnail(url=raid_stats.format(match.group(5)))
            embed.colour = discord.Colour.dark_blue()
            embed.title = match.group(6).strip(" ")
            embed.url = raid_stats.format(match.group(4))
            embed.description = "On server {}".format(match.group(9))
            embed.add_field(name="Start", value=match.group(7)).add_field(name="End", value=match.group(8))
            await client.send_message(bot_channel, embed=embed)
        else:
            await client.send_message(bot_channel,
                                      "There doesn't seem to be any raids recorded for this guild.")


@wow_lock()
@register_command("item")
async def itemname(message, bot_channel, client):
    await client.delete_message(message)
    parameters = message.content.split()
    if len(parameters) < 2:
        await client.send_message(bot_channel, "USAGE: !itemname [item name]")
        return

    item_search = " ".join(parameters[1:])

    @get_session("http://db.vanillagaming.org/?search={}".format(item_search))
    async def search_for_item(message, bot_channel, client, resp):
        return await resp.text(), resp.url

    try:
        search_doc, search_doc_url = await search_for_item(message, bot_channel, client)
    except:
        return

    embed = None

    # Three cases:
    # Case one: Several items with this name, and user must choose the correct one
    # Case two: Item found right away and we are at the item page
    # Case three: No items were found with that name
    def no_results_embed():
        embed = discord.Embed()
        embed.title = 'No results for "{}"'.format(item_search)
        embed.description = "Please try some different keywords or check your spelling."
        embed.colour = discord.Colour.dark_red()
        embed.set_thumbnail(url="http://db.vanillagaming.org/templates/wowhead/images/noresults.jpg")
        return embed

    async def create_item_embed(item_page, url):
        item_url = "db\.vanillagaming\.org/\?item=(\d+)"
        is_item = re.search(item_url, str(url))
        if is_item:
            # Subcase one
            tool_tip = re.search("class=\"tooltip\" .+?\s+?.+?class=\"(.+?)\">(.+?)</b>(.+)", item_page)
            if not tool_tip:
                await client.send_message(bot_channel,
                                          "Sorry, the web site has been changed and the bot needs an update.\n"
                                          "Please notify the developer.")
                return
            tool_tip_content = re.findall(">([^<>]+?)<", tool_tip.group(3))
            tool_tip_links = re.findall("<a href=\"(.+?)\".*?>(.+?)<", tool_tip.group(3))
            links = {k: v for v, k in tool_tip_links}
            tool_tip_description = "\n"
            not_in_set = True
            in_equip_part = -1
            for line in tool_tip_content:
                if in_equip_part == 0 and line != "Equip: ":
                    tool_tip_description += "\n"
                    in_equip_part = -1
                elif in_equip_part > 0:
                    in_equip_part -= 1
                # Formatting...
                if line in links:
                    tool_tip_description += "[{}]({})\n".format(line,
                                                                "http://db.vanillagaming.org/{}".format(links[line]))
                else:
                    if line == "Equip: ":
                        in_equip_part = 1
                        tool_tip_description += "{}".format(line)
                    elif line.endswith("Set: "):
                        if not_in_set:
                            not_in_set = False
                            tool_tip_description += "\n"
                        tool_tip_description += "{}".format(line)
                    elif line.strip(" ").startswith("(") and line.endswith(")"):
                        tool_tip_description = tool_tip_description[:-1] + "{}\n".format(line)
                    elif line == "Classes: ":
                        tool_tip_description += "{}".format(line)
                    else:
                        tool_tip_description += "{}\n".format(line)

            embed = discord.Embed()
            embed.title = tool_tip.group(2)
            embed.colour = colours[tool_tip.group(1)]
            embed.url = "http://{}".format(is_item.group(0))
            icon_name = re.search("ShowIconName.'(.+?)'.", item_page)
            if icon_name:
                embed.set_thumbnail(
                    url="http://db.vanillagaming.org/images/icons/large/{}.jpg".format(icon_name.group(1)))
            embed.description = tool_tip_description

            # Add "dropped by" or "sold by" part
            dropped_or_sold_by = re.search("id:'(dropped-by|sold-by)'.+", item_page)
            if dropped_or_sold_by:
                item_list = re.findall("{(.+?)}", dropped_or_sold_by.group(0))

                item_list_dict = list()
                for item in item_list:
                    attributes = re.compile(",(?=[a-zA-Z0-9 !'-]+?:)").split(item)
                    item_dict = dict()
                    for attribute in attributes:
                        pair = attribute.split(":")
                        item_dict[pair[0]] = pair[1]
                    item_list_dict.append(item_dict)

                if len(item_list_dict) > 0:
                    if dropped_or_sold_by.group(1) == "dropped-by" and float(item_list_dict[0]["percent"]) < 0.1:
                        embed.description += "\n{}\n".format("World Drop:")
                    else:
                        embed.description += "\n{}\n".format("Dropped By:" if dropped_or_sold_by.group(1) == "dropped-by" else "Sold By:")
                    max_items = 5
                    for item in item_list_dict[:max_items]:
                        item["react"] = ast.literal_eval(item["react"])
                        if dropped_or_sold_by.group(1) == "dropped-by":
                            if "boss" in item and item["boss"] == "'1'":
                                level = "?? (Boss)"
                            else:
                                level = "{}-{}".format(item["minlevel"], item["maxlevel"]) \
                                    if item["minlevel"] != item["maxlevel"] else item["minlevel"]
                            embed.description += "[{}]({}), Level: {}, {}, \nReact: {}, {}, %: {}\n".format(
                                item["name"].strip("'"), "http://db.vanillagaming.org/?npc={}".format(item["id"]),
                                level, "[Location](http://db.vanillagaming.org/?zone={})".format(item["location"].strip("[").strip("]")),
                                "{}{}".format("A" if item["react"][0] != -1 else "", "H" if item["react"][1] != -1 else ""),
                                "[Type](http://db.vanillagaming.org/?npcs={})".format(item["type"]), item["percent"]
                            )
                        else:
                            item["cost"] = item["cost"].strip("[").strip("]")
                            bronze = "" if len(item["cost"]) < 1 else item["cost"][-2:]
                            silver = "" if len(item["cost"]) < 3 else item["cost"][-4:-2]
                            gold = "" if len(item["cost"]) < 5 else item["cost"][:-4]

                            embed.description += "[{}]({}) ({}), Level: {}, {}, \nReact: {}, Stock: {}, Cost: {}\n".format(
                                item["name"].strip("'"), "http://db.vanillagaming.org/?npc={}".format(item["id"]), item["tag"].strip("'"),
                                "{}-{}".format(item["minlevel"], item["maxlevel"]) if item["minlevel"] != item["maxlevel"]
                                else item["minlevel"], "[Location](http://db.vanillagaming.org/?zone={})".format(item["location"].strip("[").strip("]")),
                                "{}{}".format("A" if item["react"][0] != -1 else "", "H" if item["react"][1] != -1 else ""),
                                "∞" if item["stock"] == "-1" else item["stock"], "{}{}{}".format(
                                    "{}, ".format(gold) if gold != "" else "", "{}, ".format(silver) if silver != "" else "", bronze)
                            )

        else:
            # Subcase two
            embed = no_results_embed()
        return embed

    # Case one:
    # Subcases:
    # Subcase one: Normal view with several items to choose from
    # Subcase two: Not a list of items, but something else
    search_results = re.search("Search results for .+", search_doc)
    if search_results:
        shows_items = re.search("template:'item'.+", search_doc)
        if shows_items:
            # Subcase one
            pattern = "{(.+?)}"
            item_list = re.findall(pattern, shows_items.group(0))
            item_list_dict = list()
            for item in item_list:
                attributes = re.compile(",(?=[a-zA-Z0-9 !'-]+?:)").split(item)
                item_dict = dict()
                for attribute in attributes:
                    pair = attribute.split(":")
                    item_dict[pair[0]] = pair[1]
                item_list_dict.append(item_dict)

            if len(item_list_dict) > 1:
                alternative_string = ""
                cnt = 1
                number_of_items = 15
                for item in item_list_dict[:number_of_items]:
                    alternative_string += "\n**[{}]**: {}, level {}{}".format(
                        cnt, item["name"].replace("'", "").replace("\\", "'")[1:], item["level"],
                        "" if "reqlevel" not in item else ", requirement {}".format(item["reqlevel"]))
                    cnt += 1
                alternative_string += "\n**[0]**: None of the above"

                sent_message = await client.send_message(message.channel, 'Search results for {}\n'
                                                                          'Please pick one:{}'.format(
                    item_search, alternative_string))

                def check(msg):
                    return msg.content.isdigit() and 0 <= int(msg.content) <= len(item_list_dict[:number_of_items])

                response = await client.wait_for_message(timeout=20, author=message.author, check=check)
                await client.delete_message(sent_message)
                item_dict = item_list_dict[0]
                if response:
                    await client.delete_message(response)
                    if int(response.content) == 0:
                        return
                    item_dict = item_list_dict[int(response.content) - 1]

                @get_session("http://db.vanillagaming.org/?item={}".format(item_dict["id"]))
                async def get_item_url(message, bot_channel, client, resp):
                    return await resp.text()

                response = await get_item_url(message, bot_channel, client)
                embed = await create_item_embed(response, "http://db.vanillagaming.org/?item={}".format(item_dict["id"]))
            elif len(item_list_dict) == 1:
                @get_session("http://db.vanillagaming.org/?item={}".format(item_list_dict[0]["id"]))
                async def get_item_url(message, bot_channel, client, resp):
                    return await resp.text()

                response = await get_item_url(message, bot_channel, client)
                embed = await create_item_embed(response,
                                                "http://db.vanillagaming.org/?item={}".format(item_list_dict[0]["id"]))
            else:
                embed = no_results_embed()
        else:
            # Subcase two
            embed = no_results_embed()
    else:
        # Case two:
        no_result = re.search("No results for .+", search_doc)
        if no_result:
            embed = no_results_embed()
        else:
            # Case three:
            # Subcases:
            # Subcase one: Item was found and we are now on the item page
            # Subcase two: Something else was found and we are now on that page
            embed = await create_item_embed(search_doc, search_doc_url)

    # None of the three cases
    if not embed:
        embed = no_results_embed()

    await client.send_message(bot_channel, embed=embed)


@wow_lock()
@register_command("player")
async def playername(message, bot_channel, client):
    await client.delete_message(message)
    parameters = message.content.split()
    if len(parameters) < 2:
        await client.send_message(bot_channel, "USAGE: !playername [player name]")
        return

    name = " ".join(parameters[1:])
    if not name.isalpha():
        await client.send_message(bot_channel, "Sorry, but the player name can only contain letters.")
        return

    name = name.lower().capitalize()

    try:
        player_url, player_info = await get_player_url(message, bot_channel, client, name)
    except:
        return

    @get_session(player_url)
    async def create_embed(message, bot_channel, client, resp):
        character_doc = await resp.text()

        embed = discord.Embed()
        # Retrieve name, level, icons and guild info
        player_info = re.search("class='char-name'>(.+?)<.+?class='char-level'>(.+?)<.+?"
                                "class=.+?id='(.+?)'>.+?class=.+?id='(.+?)'>(?:.+?"
                                "class='char-guild'>(.+?)<a href='(.+?)'>\&lt;(.+?)\&gt;<\/a><\/div>){0,1}",
                                character_doc)

        if not player_info:
            await client.send_message(bot_channel,
                                      "Sorry, the web site has been changed and the bot needs an update.\n"
                                      "Please notify the developer.")
            return

        server_info = re.search("<li><a href='Index\.aspx'>Home</a></li><li "
                                "class='active'><span class='divider'>/</span> (.+?)</li>", character_doc)

        if not server_info:
            await client.send_message(bot_channel,
                                      "Sorry, the web site has been changed and the bot needs an update.\n"
                                      "Please notify the developer.")
            return

        embed.set_author(name="{} {}".format(player_info.group(1), player_info.group(2)),
                         icon_url=images[player_info.group(3)], url=player_url)
        embed.set_thumbnail(url=images[player_info.group(4)])
        embed.title = "Character Info on Server {}:".format(server_info.group(1))
        embed.colour = discord.Colour.dark_blue()
        if len(player_info.groups()) > 4:
            embed.description = "{}**[{}]({})**\n".format(player_info.group(5), player_info.group(7),
                                                    'http://realmplayers.com/{}'.format(player_info.group(6)))
        else:
            embed.description = ''

        character_info = re.search('Character Info.+', character_doc)
        if not character_info:
            await client.send_message(bot_channel,
                                      "Sorry, the web site has been changed and the bot needs an update.\n"
                                      "Please notify the developer.")
            return
        character_info = character_info.group(0)

        last_seen = re.search(">Last Seen</h5>(.+?)<br/>", character_info)
        if not last_seen:
            await client.send_message(bot_channel,
                                      "Sorry, the web site has been changed and the bot needs an update.\n"
                                      "Please notify the developer.")
            return
        embed.description += "Last Seen {}\n\n".format(last_seen.group(1))

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
        embed.description += "__**Total Item Stats:**__"
        for item in item_stats_list:
            embed.description += "\n{}: **{}**".format(
                item[0], item[3] if item[3] != "" else "{} + {}".format(item[1], item[2]))
        embed.description += "\n\n__**PVP Stats:**__\n"

        rank = re.search("\WRank: (.*?)<", character_info)
        rank_progress = re.search("\WRank Progress: (.*?)<", character_info)
        standing = re.search("\WStanding: (.*?)<", character_info)
        rank_change = re.search("\WRank Change: <.*?>(.*?)<", character_info)

        embed.description += "Rank: **{}**\nRank Progress: **{}**\nStanding: **{}**\nRank Change: **{}**".format(
            "Not Available" if not rank else rank.group(1),
            "Not Available" if not rank_progress else rank_progress.group(1),
            "Not Available" if not standing else standing.group(1),
            "Not Available" if not rank_change else rank_change.group(1)
        )

        await client.send_message(bot_channel, embed=embed)

    try:
        await create_embed(message, bot_channel, client)
    except:
        return

async def prompt_user(message, bot_channel, client, name, matches, player=True):
    if len(matches) > 1:
        alternative_string = ""
        cnt = 1
        max_alternatives = 10
        for match in matches[:max_alternatives]:
            alternative_string += "\n**[{}]**: {} on server {}".format(cnt, match[1], match[2])
            cnt += 1
        alternative_string += "\n**[0]**: None of the above"
        sent_message = await client.send_message(message.channel, 'There are several {} called {}. '
                                                                  'Please pick the correct one:{}'.format(
            "players" if player else "guilds", name, alternative_string))

        def check(msg):
            return msg.content.isdigit() and 0 <= int(msg.content) <= len(matches[:max_alternatives])

        response = await client.wait_for_message(timeout=20, author=message.author, check=check)
        await client.delete_message(sent_message)
        return response


async def get_player_url(message, bot_channel, client, name):
    @get_session("http://realmplayers.com/CharacterList.aspx?search={}".format(name))
    async def get_matches(message, bot_channel, client, resp):
        name_select_doc = await resp.text()
        pattern = 'realm=(\w+?)&player=.+?\">(.+?)<\/a>.+?</font></td><td>(.+?)<\/td><td><div title='.format(name)
        return re.findall(pattern, name_select_doc)

    matches = await get_matches(message, bot_channel, client)

    if len(matches) < 1:
        await client.send_message(bot_channel, 'Sorry, could not find any player with name "{}".'.format(name))
        raise Exception

    player_tuple = matches[0]
    response = await prompt_user(message, bot_channel, client, name, matches)
    if response:
        await client.delete_message(response)
        if int(response.content) == 0:
            raise Exception
        player_tuple = matches[int(response.content) - 1]

    return "http://realmplayers.com/CharacterViewer.aspx?realm={}&player={}".format(player_tuple[0], player_tuple[1]),\
           player_tuple[:2]

images = {
    "vf-ci_druid": 'http://images.wikia.com/wowwiki/images/6/6f/Ui-charactercreate-classes_druid.png',
    "vf-ci_warrior": 'http://images.wikia.com/wowwiki/images/3/37/Ui-charactercreate-classes_warrior.png',
    "vf-ci_shaman": 'http://images.wikia.com/wowwiki/images/3/3e/Ui-charactercreate-classes_shaman.png',
    "vf-ci_priest": 'http://images.wikia.com/wowwiki/images/0/0f/Ui-charactercreate-classes_priest.png',
    "vf-ci_mage": 'http://images.wikia.com/wowwiki/images/5/56/Ui-charactercreate-classes_mage.png',
    "vf-ci_rogue": 'http://images.wikia.com/wowwiki/images/b/b1/Ui-charactercreate-classes_rogue.png',
    "vf-ci_warlock": 'http://images.wikia.com/wowwiki/images/c/cf/Ui-charactercreate-classes_warlock.png',
    "vf-ci_hunter": 'http://images.wikia.com/wowwiki/images/4/4e/Ui-charactercreate-classes_hunter.png',
    "vf-ci_paladin": 'http://images.wikia.com/wowwiki/images/8/80/Ui-charactercreate-classes_paladin.png',

    "vf-ri_male_undead": 'http://images2.wikia.nocookie.net/__cb20070124143003/wowwiki/images/b/b3/Ui-charactercreate-races_undead-male.png',
    "vf-ri_male_orc": 'http://images2.wikia.nocookie.net/__cb20070124142837/wowwiki/images/3/35/Ui-charactercreate-races_orc-male.png',
    "vf-ri_male_tauren": 'http://images4.wikia.nocookie.net/__cb20070124142903/wowwiki/images/7/78/Ui-charactercreate-races_tauren-male.png',
    "vf-ri_male_troll": 'http://images4.wikia.nocookie.net/__cb20070124142933/wowwiki/images/d/d7/Ui-charactercreate-races_troll-male.png',
    "vf-ri_male_bloodelf": 'http://img1.wikia.nocookie.net/__cb20070124142421/wowwiki/images/c/cc/Ui-charactercreate-races_bloodelf-male.png',
    "vf-ri_male_human": 'http://images3.wikia.nocookie.net/__cb20070124142722/wowwiki/images/e/eb/Ui-charactercreate-races_human-male.png',
    "vf-ri_male_dwarf": 'http://images2.wikia.nocookie.net/__cb20070124142516/wowwiki/images/f/f5/Ui-charactercreate-races_dwarf-male.png',
    "vf-ri_male_gnome": 'http://images1.wikia.nocookie.net/__cb20070124142654/wowwiki/images/a/a9/Ui-charactercreate-races_gnome-male.png',
    "vf-ri_male_nightelf": 'http://images4.wikia.nocookie.net/__cb20070124142757/wowwiki/images/1/12/Ui-charactercreate-races_nightelf-male.png',
    "vf-ri_male_draenei": 'http://img2.wikia.nocookie.net/__cb20070124142450/wowwiki/images/0/04/Ui-charactercreate-races_draenei-male.png',

    "vf-ri_female_undead": 'http://images4.wikia.nocookie.net/__cb20070124142948/wowwiki/images/4/4d/Ui-charactercreate-races_undead-female.png',
    "vf-ri_female_orc": 'http://images2.wikia.nocookie.net/__cb20070124142826/wowwiki/images/3/38/Ui-charactercreate-races_orc-female.png',
    "vf-ri_female_tauren": 'http://images1.wikia.nocookie.net/__cb20070124142854/wowwiki/images/4/48/Ui-charactercreate-races_tauren-female.png',
    "vf-ri_female_troll": 'http://images2.wikia.nocookie.net/__cb20070124142916/wowwiki/images/b/b9/Ui-charactercreate-races_troll-female.png',
    "vf-ri_female_bloodelf": 'http://img3.wikia.nocookie.net/__cb20070124142406/wowwiki/images/f/f6/Ui-charactercreate-races_bloodelf-female.png',
    "vf-ri_female_human": 'http://images2.wikia.nocookie.net/__cb20070124142708/wowwiki/images/7/79/Ui-charactercreate-races_human-female.png',
    "vf-ri_female_dwarf": 'http://images2.wikia.nocookie.net/__cb20070124142506/wowwiki/images/b/b1/Ui-charactercreate-races_dwarf-female.png',
    "vf-ri_female_gnome": 'http://images3.wikia.nocookie.net/__cb20070124142633/wowwiki/images/7/7b/Ui-charactercreate-races_gnome-female.png',
    "vf-ri_female_nightelf": 'http://images1.wikia.nocookie.net/__cb20070124142738/wowwiki/images/a/a7/Ui-charactercreate-races_nightelf-female.png',
    "vf-ri_female_draenei": 'http://img3.wikia.nocookie.net/__cb20070124142432/wowwiki/images/b/b3/Ui-charactercreate-races_draenei-female.png'
}

colours = {
    "q1": discord.Colour.dark_grey(),
    "q2": discord.Colour.dark_green(),
    "q3": discord.Colour.dark_blue(),
    "q4": discord.Colour.dark_purple(),
    "q5": discord.Colour.dark_orange()
}

raid_icons = {
    "Zul'Gurub": "http://realmplayers.com/RaidStats/assets/img/raid/raid-zulgurub.png",
    "Molten Core": "http://realmplayers.com/RaidStats/assets/img/raid/raid-moltencore.png",
    "Onyxia's Lair": "http://realmplayers.com/RaidStats/assets/img/raid/raid-onyxia.png",
    "Karazhan": "http://realmplayers.com/RaidStats/assets/img/raid/raid-karazhan.gif",
    "Blackwing Lair": "http://realmplayers.com/RaidStats/assets/img/raid/raid-blackwinglair.png",
    "Tempest Keep": "http://realmplayers.com/RaidStats/assets/img/raid/raid-tempestkeep.gif",
    "Naxxramas": "http://realmplayers.com/RaidStats/assets/img/raid/raid-naxxramas.png",
    "Serpentshrine Cavern": "http://realmplayers.com/RaidStats/assets/img/raid/raid-serpentshrinecavern.gif",
    "Ruins of Ahn'Qiraj": "http://realmplayers.com/RaidStats/assets/img/raid/raid-aqruins.png",
    "Ahn'Qiraj Temple": "http://realmplayers.com/RaidStats/assets/img/raid/raid-aqtemple.png",
    "Magtheridon's Lair": "http://realmplayers.com/RaidStats/assets/img/raid/raid-magtheridon.gif",
    "Gruul's Lair": "http://realmplayers.com/RaidStats/assets/img/raid/raid-gruul.gif",
    "Black Temple": "http://realmplayers.com/RaidStats/assets/img/raid/raid-blacktemple.gif",
    "Hyjal Summit": "http://realmplayers.com/RaidStats/assets/img/raid/raid-hyjalsummit.gif",
    "Sunwell Plateau": "http://realmplayers.com/RaidStats/assets/img/raid/raid-sunwellplateau.gif"
}

race_icons = {
    "horde": "http://realmplayers.com/RaidStats/assets/img/Horde_32.png",
    "alliance": "http://realmplayers.com/RaidStats/assets/img/Alliance_32.png"
}

# Not currently used, but it exists and might come in handy in the future
server_abbreviation = {
    "REB": "Rebirth",
    "KRO": "Kronos",
    "KR2": "Kronos II",
    "VG": "VanillaGaming",
    "Ely": "Elysium",
    "ZeK": "Zeth'Kur",
    "Ana": "Anathema",
    "Dar": "Darrowshire",
    "NEF": "Nefarian(DE)",
    "NG": "NostalGeek(FR)",
    "NES": "Nemesis",
    "NST": "Nostralia",
    "ELY": "Elysium(Old)",
    "WS2": "Warsong(Feenix)",
    "ArA": "Archangel",
    "VWH": "Wildhammer",
    "VST": "Stonetalon",
    "EXC": "ExcaliburTBC",
    "HG": "WarGate",
    "HLF": "Hellfire I",
    "HF2": "Hellfire II",
    "OUT": "Outland",
    "MDV": "Medivh",
    "FLM": "Felmyst",
    "FMW": "Firemaw",
    "AR": "Ares"
}