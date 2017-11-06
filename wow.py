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
        await client.send_message(bot_channel, "USAGE: !lastraidplayer [player name] or !lastraidguild [guild name]")
        return

    name = parameters[1]
    if not name.isalpha():
        await client.send_message(bot_channel, "Sorry, but the {} name can only contain letters.".format("player" if player else "guild"))
        return

    name = parameters[1].lower().capitalize()
    raid_link = "http://realmplayers.com/RaidStats/RaidList.aspx?realm={}&guild={}"
    if player:
        try:
            player_url = await get_player_url(message, bot_channel, client, name)
        except:
            return

        # Get guild url from the player
        @get_session(player_url)
        async def get_guild_url(message, bot_channel, client, resp):
            player_doc = await resp.text()
            pattern = "class='char-guild'>.+?<a href='GuildViewer\.aspx\?realm=(\w+?)\&guild=(\w+?)'>"
            return re.search(pattern, player_doc)

        try:
            match = await get_guild_url(message, bot_channel, client)
        except:
            return

        if match:
            raid_link = raid_link.format(match.group(1), match.group(2))
        else:
            await client.send_message(bot_channel, "The given player doesn't seem to be part of any guilds.")
            return
    else:
        # Get guild url from searching after the guild
        @get_session("http://realmplayers.com/CharacterList.aspx?search={}".format(name))
        async def get_guild_url(message, bot_channel, client, resp):
            search_doc = await resp.text()
            pattern = 'realm=(\w+?)&guild=({0})\">&lt;({0})&gt;<\/a>'.format(name)
            return re.findall(pattern, search_doc)

        try:
            matches = await get_guild_url(message, bot_channel, client)
        except:
            return

        if len(matches) < 1:
            await client.send_message(bot_channel, 'Sorry, could not find any player with name "{}".'.format(name))
            return

        guild_tuple = matches[0]
        response = await prompt_user(message, bot_channel, client, name, matches)
        if response:
            await client.delete_message(response)
            guild_tuple = matches[int(response.content) - 1]

        raid_link = raid_link.format(guild_tuple[0], guild_tuple[1])

    # Get raid link
    @get_session(raid_link)
    async def get_last_raid_url(message, bot_channel, client, resp):
        search_doc = await resp.text()
        pattern = '<a href="(.+?)"><img src="(.+?)"\/>(.+?)<\/a><\/td><td><a href="(.+?)"><img src="(.+?)"\/>(.+?)<\/a><\/td><td>(.+?)<\/td><td>(.+?)<\/td><td>(.+?)<\/td><\/tr>'
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
    # Case two: No items were found with that name
    # Case three: Item found right away and we are at the item page
    def no_results_embed():
        embed = discord.Embed()
        embed.title = 'No results for "{}"'.format(item_search)
        embed.description = "Please try some different keywords or check your spelling."
        embed.colour = discord.Colour.dark_red()
        embed.set_thumbnail(url="http://db.vanillagaming.org/templates/wowhead/images/noresults.jpg")
        return embed

    # Case one:
    # Subcases:
    # Subcase one: Normal view with several items to choose from
    # Subcase two: Not a list of items, but something else
    search_results = re.search("Search results for .+", search_doc)
    if search_results:
        shows_items = re.search("template:'item'", search_doc)
        if shows_items:
            # Subcase one
            pattern = ""
            item_list = re.findall(pattern, search_doc)
            if len(item_list) > 0:
                alternative_string = ""
                cnt = 1
                number_of_items = 5
                for item in item_list[:number_of_items]:
                    alternative_string += "\n**[{}]**: {}, level {}, requirement {}, type {}".format(cnt, item[0], item[1], item[2], item[3])
                    cnt += 1

                sent_message = await client.send_message(message.channel, 'Search results for {}\n'
                                                                          'Please pick one:{}'.format(
                    item_search, alternative_string))

                def check(msg):
                    return msg.content.isdigit() and 0 < int(msg.content) <= number_of_items

                response = await client.wait_for_message(timeout=20, author=message.author, check=check)
                await client.delete_message(sent_message)
                item_tuple = item_list[0]
                if response:
                    await client.delete_message(response)
                    item_tuple = item_list[int(response.content) - 1]

                @get_session("")
                async def get_item_url(message, bot_channel, client, resp):
                    return await resp.text()

            else:
                embed = no_results_embed()
        else:
            # Subcase two
            embed = no_results_embed()

    # Case two:
    no_result = re.search("No results for .+", search_doc)
    if no_result:
        embed = no_results_embed()

    # Case three:
    # Subcases:
    # Subcase one: Item was found and we are now on the item page
    # Subcase two: Something else was found and we are now on that page
    item_url = "db\.vanillagaming\.org/\?item=(\d+)"
    is_item = re.search(item_url, str(search_doc_url))
    if is_item:
        # Subcase one
        tool_tip = re.search("class=\"q3\">(.+?)</b>(.+)", search_doc)
        if not tool_tip:
            await client.send_message(bot_channel,
                                      "Sorry, the web site has been changed and the bot needs an update.\n"
                                      "Please notify the developer.")
            return
        tool_tip_content = re.findall(">([^\/<>]+?)<", tool_tip.group(2))
        tool_tip_description = ""
        for line in tool_tip_content:
            tool_tip_description += "\n{}".format(line)

        embed = discord.Embed()
        embed.title = tool_tip.group(1)
        embed.colour = discord.Colour.dark_blue()
        embed.url = "http://{}".format(is_item.group(0))
        icon_name = re.search("ShowIconName.'(.+?)'.", search_doc)
        if icon_name:
           embed.set_thumbnail(url="http://db.vanillagaming.org/images/icons/large/{}.jpg".format(icon_name.group(1)))
        embed.description = tool_tip_description
    else:
        # Subcase two
        embed = no_results_embed()

    # None of the three cases
    if not embed:
        embed = no_results_embed()

    await client.send_message(bot_channel, embed=embed)


async def playername(message, bot_channel, client):
    await client.delete_message(message)
    parameters = message.content.split()
    if len(parameters) < 2:
        await client.send_message(bot_channel, "USAGE: !playername [player name]")
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
        for match in matches:
            alternative_string += "\n**[{}]**: {} on server {}".format(cnt, match[1], match[0])
            cnt += 1

        sent_message = await client.send_message(message.channel, 'There are several {} called {}. '
                                                                  'Please pick the correct one:{}'.format(
            "players" if player else "guilds", name, alternative_string))

        def check(msg):
            return msg.content.isdigit() and 0 < int(msg.content) <= len(matches)

        response = await client.wait_for_message(timeout=20, author=message.author, check=check)
        await client.delete_message(sent_message)
        return response


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
    response = await prompt_user(message, bot_channel, client, name, matches)
    if response:
        await client.delete_message(response)
        player_tuple = matches[int(response.content) - 1]

    return "http://realmplayers.com/CharacterViewer.aspx?realm={}&player={}".format(player_tuple[0], player_tuple[1])

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
