import rocket_snake
import discord
import traceback

async def get_rl_rank(message, bot_channel, client):
    await client.delete_message(message)
    rl_client = rocket_snake.RLS_Client("EQJLFCC1HG2RIV2PHW7WDLW077DCPSX5")
    parameters = message.content.split()
    if len(parameters) > 1:
        try:
            player = await rl_client.get_player(parameters[1], rocket_snake.constants.STEAM)
            embed = discord.Embed()
            embed.title = "Season {} ranks:".format(str(len(player.ranked_seasons)))
            embed.colour = discord.Colour.purple()
            latest_season = player.ranked_seasons[str(len(player.ranked_seasons))]
            solo_duel = 'No rank' if '10' not in latest_season else latest_season['10'].rankPoints
            doubles = 'No rank' if '11' not in latest_season else latest_season['11'].rankPoints
            solo_standard = 'No rank' if '12' not in latest_season else latest_season['12'].rankPoints
            standard = 'No rank' if '13' not in latest_season else latest_season['13'].rankPoints
            embed.set_image(url=player.signature_url).set_thumbnail(url=player.avatar_url)\
                .add_field(name='Solo Duel', value='{} points'.format(solo_duel)).add_field(name='Solo Standard', value='{} points'.format(solo_standard)) \
                .add_field(name='Doubles', value='{} points'.format(doubles)).add_field(name='Standard', value='{} points'.format(standard))
            await client.send_message(bot_channel, "{}:".format(message.author.name), embed=embed)
        except rocket_snake.exceptions.APINotFoundError:
            await client.send_message(bot_channel, "{}: Sorry, couldn't find player!".format(message.author.name))
        except:
            traceback.print_exc()
            await client.send_message(bot_channel, "{}: Sorry, something went wrong fetching the stats!\n"
                                                   "Please try again later.".format(message.author.name))
