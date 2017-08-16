import rocket_snake

async def get_rl_rank(message, bot_channel, client):
    await client.delete_message(message)
    rl_client = rocket_snake.RLS_Client("EQJLFCC1HG2RIV2PHW7WDLW077DCPSX5")
    parameters = message.content.split()
    if len(parameters) > 1:
        try:
            player = await rl_client.get_player(parameters[1], rocket_snake.constants.STEAM)
            player_info = "Rocket League player {} on {}\nStats: {}\n" \
                          "Rank Season 5: {}".format(player.display_name, player.platform,
                                                     player.stats, player.ranked_seasons['5'])
            await client.send_message(bot_channel, "{}: {}".format(message.author.name,player_info))
        except rocket_snake.exceptions.APINotFoundError:
            await client.send_message(bot_channel, "{}: Sorry, couldn't find player!".format(message.author.name))
        except:
            await client.send_message(bot_channel, "{}: Sorry, something went wrong fetching the stats!\n"
                                                   "Please try again later.".format(message.author.name))
