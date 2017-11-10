import re
import threading
import urllib.request
import steamapi

import math
import rocket_snake
import discord
import traceback

import time

from utils import register_command


@register_command("rlstats", "getrlrank", "rlrank")
async def get_rl_rank(message, bot_channel, client):
    await client.delete_message(message)
    rl_client = rocket_snake.RLS_Client("EQJLFCC1HG2RIV2PHW7WDLW077DCPSX5")
    parameters = message.content.split()
    if len(parameters) > 1:
        try:
            player = await rl_client.get_player(parameters[1], rocket_snake.constants.STEAM)
            seasons = await rl_client.get_seasons()
            last_season = next((season for season in seasons if season.is_current), seasons[-1])
            embed = discord.Embed()
            embed.title = "Season {} ranks:".format(str(last_season.id))
            embed.colour = discord.Colour.purple()
            latest_season = player.ranked_seasons[str(last_season.id)]
            solo_duel = 'No rank' if '10' not in latest_season else latest_season['10'].rankPoints
            doubles = 'No rank' if '11' not in latest_season else latest_season['11'].rankPoints
            solo_standard = 'No rank' if '12' not in latest_season else latest_season['12'].rankPoints
            standard = 'No rank' if '13' not in latest_season else latest_season['13'].rankPoints
            embed.set_image(url=player.signature_url).set_thumbnail(url=player.avatar_url)\
                .add_field(name='Solo Duel', value='{} points'.format(solo_duel)).add_field(name='Solo Standard', value='{} points'.format(solo_standard)) \
                .add_field(name='Doubles', value='{} points'.format(doubles)).add_field(name='Standard', value='{} points'.format(standard))\
                .set_footer(text='The signature is cached by Discord for a day or two. '
                                 'See the original site for updated signature.')
            await client.send_message(bot_channel, "{}:".format(message.author.name), embed=embed)
        except rocket_snake.exceptions.APINotFoundError:
            await client.send_message(bot_channel, "{}: Sorry, couldn't find player!".format(message.author.name))
        except:
            traceback.print_exc()
            await client.send_message(bot_channel, "{}: Sorry, something went wrong fetching the stats!\n"
                                                   "Please try again later.".format(message.author.name))


@register_command("sharedgames")
async def sharedgames(message, bot_channel, client):
    await client.delete_message(message)
    content = message.content.split()
    users = content[1:]
    api_interface = steamapi.core.APIConnection(api_key="BDCD48F7FF3046773D26D94F742B0B54", validate_key=True)

    class SharedGame:
        def __init__(self, game):
            self.game = game
            self.total_playtime_forever = game.playtime_forever

        def add_together_playtime(self, game):
            self.total_playtime_forever += game.playtime_forever
            return self

    sharedgames_list = list()
    first_injection = True
    user_string = str()
    print("Starting user game list retrieval...")
    start = time.time()
    for user in users:
        try:
            steam_user = steamapi.user.SteamUser(userurl=user)
        except steamapi.errors.UserNotFoundError:
            continue
        user_string += "**{}**, ".format(steam_user.name)
        games = steam_user.games
        if first_injection:
            sharedgames_list = list(map(lambda game: SharedGame(game), games))
            first_injection = False
        else:
            sharedgames_list = list(filter(lambda shared_game: shared_game.game in games, sharedgames_list))
            sharedgames_list = list(map(lambda shared_game: shared_game.add_together_playtime(games[games.index(shared_game.game)]), sharedgames_list))
    print("Done! It took {} seconds.".format(time.time()-start))
    if first_injection:
        await client.send_message(bot_channel, "Sorry, could not find any users...")
        return
    print("Starting game info retrieval...")
    start = time.time()
    print_string = str()
    cnt = 1
    sharedgames_list_temp = list()

    def games_filter(shared_game):
        url = urllib.request.urlopen("http://store.steampowered.com/app/{}".format(shared_game.game.appid)).read().decode('utf-8')
        if re.search(">Multi-player</a>", url) or re.search(">Co-op</a>", url):
            sharedgames_list_temp.append(shared_game)
    thread_list = list()
    for game in sharedgames_list:
        thread = threading.Thread(target=games_filter, args=[game])
        thread.start()
        thread_list.append(thread)
    for thread in thread_list:
        thread.join()
    sharedgames_list = sharedgames_list_temp
    sharedgames_list = sorted(sharedgames_list, key=lambda shared_game: shared_game.total_playtime_forever, reverse=True)
    print("Done! It took {} seconds.".format(time.time()-start))
    for shared_game in sharedgames_list:
        print_string += "{}. {}   **{} hours total**\n".format(cnt, shared_game.game.name, math.ceil(shared_game.total_playtime_forever/60))
        cnt += 1
        if cnt == 40:
            break
    await client.send_message(bot_channel, "{} share these games:\n{}".format(user_string[:-2], print_string))
