import utils
import time


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

    response = await client.wait_for_message(timeout=60, author=message.author)
    while response and response.content != 'done':
        await client.delete_message(response)
        member.options.append(response.content)
        response = await client.wait_for_message(timeout=60, author=message.author)

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
                              'Poll question: **{}**'.format(member.question))
    await client.send_message(message.channel,
                              'Alternatives:\n')

    counter = 0;
    for string in member.options:
        counter += 1
        await client.send_message(message.channel,
                                  '**{}: {}**'.format(counter, string))

    await client.send_message(message.channel,
                              'You now have 30 seconds to vote.'
                              '\nTo extend voting time by 30 seconds use !ext.'
                              '\nTo vote react to each option or use !vote [index].')


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
    while server.poll_time > 0:
        time.sleep(1)
        server.poll_time -= 1
        # Need code her til store votes, both index and react voting

    await client.send_message(message.channel,
                              'Vote complete! Calculating results')
