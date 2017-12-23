import discord
import pymongo

import events

client = None


def run_bot():
    global client
    client = discord.Client()

    db_client = pymongo.MongoClient("mongodb://Ohminator:an4MgtGkIlgOLo0h@ohminator-cluster-shard-00-00-it3lf.mongodb.net:27017,ohminator-cluster-shard-00-01-it3lf.mongodb.net:27017,ohminator-cluster-shard-00-02-it3lf.mongodb.net:27017/Ohminator?ssl=true&replicaSet=Ohminator-cluster-shard-0&authSource=admin")
    db = db_client.Ohminator

    # Contains all events in the event loop and all event handling pluss setup of datastructure
    events.Events(client, db)

    # Reads token
    with open("token.txt", 'r') as f:
        token = f.read().strip()

    # Starts the execution of the bot
    client.run(token)

async def run_bot_coroutine(loop=None):
    global client
    client = discord.Client()

    db_client = pymongo.MongoClient(
        "mongodb://Ohminator:an4MgtGkIlgOLo0h@ohminator-cluster-shard-00-00-it3lf.mongodb.net:27017,ohminator-cluster-shard-00-01-it3lf.mongodb.net:27017,ohminator-cluster-shard-00-02-it3lf.mongodb.net:27017/Ohminator?ssl=true&replicaSet=Ohminator-cluster-shard-0&authSource=admin")
    db = db_client.Ohminator

    # Contains all events in the event loop and all event handling pluss setup of datastructure
    events.Events(client, db)

    # Reads token
    with open("token.txt", 'r') as f:
        token = f.read().strip()

    # Starts the execution of the bot
    await client.start(token)

if __name__ == '__main__':
    run_bot()
