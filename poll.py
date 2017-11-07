import utils
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


# ToDo:
# 1: Fikse problemet med en poll per kanal. - Done
# 2: Fikse random sletting av siste bot utskift (dette skjer når voting skal starte). - Done
# 3: Fikse alternativ utskriften til bilde. - Done

# 4: Fikse en option for votes per users.
# 5: Mulighet for tidsramme på polls
# 6: Rydde oppe i kode og utskrifter så det ser så pent ut som mulig.
# 7: Dokumentasjon

async def get_question_and_alt(message, bot_channel, client):
    parameters = message.content.split()
    if len(parameters) < 2:
        await client.send_message(message.channel,
                                  '{}: Use: !poll [question]'
                                  .format(message.author.name))
        return
    server = utils.get_server(message.server)
    channel = server.get_channel(message.channel.id)

    if not channel.question:
        question = " ".join(parameters[1:])
        channel.question = question
    else:
        await client.send_message(message.channel,
                                  'Only one poll per channel allowed at the same time')
        return

    await client.send_message(message.channel,
                              'Question received: {}'.format(question))

    await client.send_message(message.channel,
                              'What alternatives do you like for this poll?'
                              '\nType done when finished.\n'
                              'Timeout after 2 min with out a new alternativ.')

    option = await client.wait_for_message(timeout=120, author=message.author)

    if not option:
        await client.send_message(message.channel,
                                  'No alternatives received in 120 seconds. Terminating poll...')
        clean_up(message)
        return

    while option and option.content != 'done':
        await client.delete_message(option)
        channel.options.append(option)
        option = await client.wait_for_message(timeout=120, author=message.author)

    if len(channel.options) < 2:
        await client.send_message(message.channel,
                                  'Need two or more alternatives. Terminating poll...')
        clean_up(message)
        return

    await vote_question(message, bot_channel, client)


async def see_question(message, bot_channel, client):
    server = utils.get_server(message.server)
    channel = server.get_channel(message.channel.id)
    if not channel.question:
        await client.send_message(bot_channel,
                                  'No poll initiated!'
                                  '\nWhy dont you start one! Use: !poll [question]')
    else:
        await client.send_message(message.channel,
                                  'Question is: {}'.format(channel.question))


async def print_q_and_a(message, bot_channel, client):
    server = utils.get_server(message.server)
    channel = server.get_channel(message.channel.id)
    await client.send_message(message.channel,
                              'Start your voting peps! '
                              '\nTo vote react to each option!.'
                              '\nWhen voting is complete type done')

    await client.send_message(message.channel,
                              'Poll question: **{}** {}Alternatives:\n'.format(channel.question, '\n'))

    counter = 0;
    alternatives = list()
    for string in channel.options:
        counter += 1
        alternatives.append(await client.send_message(message.channel,
                                                      '**{}: {}**'.format(counter, string.content)))

    channel.options = alternatives


async def vote_question(message, bot_channel, client):
    await print_q_and_a(message, bot_channel, client)
    server = utils.get_server(message.server)
    channel = server.get_channel(message.channel.id)
    tempoptions = list()

    option_message = await client.wait_for_message(timeout=None, channel=message.channel)
    while option_message and option_message.content != 'done':
        option_message = await client.wait_for_message(timeout=None, channel=message.channel)
        await client.delete_message(option_message)


    for option_message in channel.options:
        temp = await client.get_message(option_message.channel, option_message.id)
        tempoptions.append(temp)

    for index in range(0, len(channel.options)):
        channel.options[index] = tempoptions[index]

    for msg in channel.options:
        counter = 0
        for reaction in msg.reactions:
            counter += reaction.count

        channel.result.append(counter)

    await client.send_message(message.channel,
                              'Vote complete! Calculating results')

    make_dict_of_alt(message)

    # If no body votes:
    count = 0
    for x in range(len(channel.result)):
        if channel.result[x] == 0:
            count += 1

    if count == len(channel.result):
        await client.send_message(message.channel,
                                  'Nobody voted, poll terminated!')
        clean_up(message)
        return

    for alt in channel.options:
        await client.send_message(message.channel,
                                  '**Alt** {}'.format(alt.content))

    await make_pyplot(message, bot_channel, client)

    clean_up(message)


def clean_up(message):
    server = utils.get_server(message.server)
    channel = server.get_channel(message.channel.id)
    channel.dict.clear()
    channel.options.clear()
    channel.result.clear()
    channel.question = None


def make_dict_of_alt(message):
    server = utils.get_server(message.server)
    channel = server.get_channel(message.channel.id)

    for res in range(len(channel.result)):
        channel.dict['Alt {}'.format(res + 1)] = channel.result[res]


# Make nice and pretty graph of the results from voting
async def make_pyplot(message, bot_channel, client):
    server = utils.get_server(message.server)
    server.get_channel(message.channel.id)
    channel = server.get_channel(message.channel.id)

    ax = plt.figure().gca()
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    plt.title('Question: {}'.format(channel.question))
    plt.xlabel("Alternatives")
    plt.ylabel("Votes")
    plt.bar(range(len(channel.dict)), channel.dict.values(), align='center')
    plt.xticks(range(len(channel.dict)), channel.dict.keys())

    plt.savefig('servers/{}/channels/{}/foo.png'.format(server.server_loc,
                                                        server.get_channel(message.channel.id).channel_loc))
    await client.send_file(message.channel,
                           'servers/{}/channels/{}/foo.png'.format(server.server_loc,
                                                                   server.get_channel(message.channel.id).channel_loc))
