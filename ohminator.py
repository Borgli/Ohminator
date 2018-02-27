import traceback
import asyncio
import discord
import pymongo

from events import Events


def main():
    client = discord.Client()

    # Reads MongoDB connection parameter as it has sensitive information
    with open('mongodb-connection-parameter.txt', 'r') as f:
        mongodb_connection_parameter = f.read().strip()

    db_client = pymongo.MongoClient(mongodb_connection_parameter)
    db = db_client.Ohminator

    # Contains all events in the event loop and all event handling
    events = Events(client, db)

    # Reads token
    with open("token.txt", 'r') as f:
        token = f.read().strip()

    # Starts the execution of the bot
    client.run(token)


if __name__ == '__main__':
    while True:
        # Will automatically restart the bot
        # The wrapper will catch KeyboardInterrupts, so any exception that occurs means restart
        try:
            main()
        except:
            traceback.print_exc()
            asyncio.set_event_loop(asyncio.new_event_loop())
            continue
        break
