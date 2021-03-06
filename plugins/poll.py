import utils
from utils import register_command


# Handle issue with more then one poll
@register_command("poll")
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


@register_command("question?")
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
                                                      '**{}: {}**'.format(counter, string.content)))

    member.options = alternatives

    await client.send_message(message.channel,
                              'Start your voting peps! '
                              '\nTo vote react to each option!.'
                              '\nWhen voting is complete type done')


# not in use - Refactor at later time
@register_command("ext")
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
            counter =+ reaction.count

        await client.send_message(message.channel,
                                  '{}'.format(counter))

    await client.send_message(message.channel,
                                'Vote complete! Calculating results')


        # Make nice and pretty graph of the results from voting


def make_pyplot():
    print("hei")
