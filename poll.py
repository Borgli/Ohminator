import utils


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
                              'What alternatives do you like for this poll? (timeout @ 60 sec)'
                              '\nType done when finished.')

    response = await client.wait_for_message(timeout=10, author=message.author)
    while response and response.content != 'done':
        await client.delete_message(response)
        member.options.append(response.content)
        response = await client.wait_for_message(timeout=10, author=message.author)

    await print_q_and_a(message, bot_channel, client)


async def see_question(message, bot_channel, client):
    server = utils.get_server(message.server)
    member = server.get_member(message.author.id)
    if not member.question:
        await client.send_message(bot_channel,
                                  'No poll initiated!'
                                  '\n Why dont you start one! Use: !poll [question]')
    else:
        await client.send_message(message.channel,
                                  'Question is: {}'.format(member.question))


async def print_q_and_a(message, bot_channel, client):
    server = utils.get_server(message.server)
    member = server.get_member(message.author.id)
    await client.send_message(message.channel,
                              'Poll question: **{}**'.format(member.question))
    await client.send_message(message.channel,
                              'Alternatives:\n')
    for string in member.options:
        await client.send_message(message.channel,
                                  '**{}**'.format(string))