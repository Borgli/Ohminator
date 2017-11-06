import utils
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import os

# Handel issue with more then one poll
async def get_question(message, bot_channel, client):
    parameters = message.content.split()
    if len(parameters) < 2:
        await client.send_message(message.channel,
                                  '{}: Use: !poll [question]'.format(message.author.name))
        return
    server = utils.get_server(message.server)
    member = server.get_member(message.author.id)
    question = " ".join(parameters[1:])
    member.question = question

    await client.send_message(message.channel,
                              'Question received: {}'.format(question))

    await client.send_message(message.channel,
                              'What alternatives do you like for this poll?'
                              '\nType done when finished.')

    option = await client.wait_for_message(timeout=60, author=message.author)
    while option and option.content != 'done':
        await client.delete_message(option)
        member.options.append(option)
        option = await client.wait_for_message(timeout=60, author=message.author)

    await vote_question(message, bot_channel, client)


async def see_question(message, bot_channel, client):
    server = utils.get_server(message.server)
    member = server.get_member(message.author.id)
    if not member.question:
        await client.send_message(bot_channel,
                                  'No poll initiated!'
                                  '\nWhy dont you start one! Use: !poll [question]')
    else:
        await client.send_message(message.channel,
                                  'Question is: {}'.format(member.question))


async def print_q_and_a(message, bot_channel, client):
    server = utils.get_server(message.server)
    member = server.get_member(message.author.id)
    await client.send_message(message.channel,
                              'Poll question: **{}**        {}Alternatives:\n'.format(member.question, '\n'))

    counter = 0;
    alternatives = list()
    for string in member.options:
        counter += 1
        alternatives.append(await client.send_message(message.channel,
                                                      '{}: {}'.format(counter, string.content)))

    member.options = alternatives

    await client.send_message(message.channel,
                              'Start your voting peps! '
                              '\nTo vote react to each option!.'
                              '\nWhen voting is complete type done')


# not in use - Refactor at later time
async def extend_time(message, bot_channel, client):
    await client.delete_message(message)
    server = utils.get_server(message.server)
    member = server.get_member(message.author.id)
    if member.question is None:
        await client.send_message(bot_channel,
                                  'No poll initiated!'
                                  '\nWhy dont you start one! Use: !poll [question]')
    else:
        server.poll_time += 30
        await client.send_message(message.channel,
                                  'Time remaining to vote is now: {}'.format(server.poll_time))


async def vote_question(message, bot_channel, client):
    await print_q_and_a(message, bot_channel, client)
    server = utils.get_server(message.server)
    member = server.get_member(message.author.id)
    tempoptions = list()

    option_message = await client.wait_for_message(timeout=None, channel=message.channel)
    while option_message and option_message.content != 'done':
        await client.delete_message(option_message)
        option_message = await client.wait_for_message(timeout=None, channel=message.channel)

    for option_message in member.options:
        temp = await client.get_message(option_message.channel, option_message.id)
        tempoptions.append(temp)

    for index in range(0, len(member.options)):
        member.options[index] = tempoptions[index]

    for msg in member.options:
        counter = 0;
        for reaction in msg.reactions:
            counter += reaction.count

        member.result.append(counter)

    await client.send_message(message.channel,
                              'Vote complete! Calculating results')

    make_dict_of_alt(message)
    count = 0
    for x in range(len(member.result)):
        if member.result[x] == 0:
            count += 1

    if count == len(member.result):
        await client.send_message(message.channel,
                                  'Nobody voted, poll terminated!')
        return

    await make_pyplot(message, bot_channel, client)

    member.dict.clear()
    member.options.clear()
    member.result.clear()


def make_dict_of_alt(message):
    server = utils.get_server(message.server)
    member = server.get_member(message.author.id)

    for res in range(len(member.result)):
        member.dict[member.options[res].content] = member.result[res];


# Make nice and pretty graph of the results from voting
async def make_pyplot(message, bot_channel, client):
    server = utils.get_server(message.server)
    member = server.get_member(message.author.id)
    server.get_channel(message.channel.id)

    ax = plt.figure().gca()
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.xlabel("Alternatives")
    plt.ylabel("Votes")
    plt.bar(range(len(member.dict)), member.dict.values(), align='center')
    plt.xticks(range(len(member.dict)), member.dict.keys())

    plt.savefig('servers/{}/members/{}/foo.png'.format(server.server_loc,
                                                       server.get_channel(message.channel.id).channel_loc))
    await client.send_file(message.channel,
                           'servers/{}/members/{}/foo.png'.format(server.server_loc,
                                                                  server.get_channel(message.channel.id).channel_loc))
