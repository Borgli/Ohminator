import discord
import pymongo

import events

client = discord.Client()

# Reads MongoDB connection parameter as it has sensitive information
with open('mongodb-connection-parameter.txt', 'r') as f:
    mongodb_connection_parameter = f.read().strip()

db_client = pymongo.MongoClient(mongodb_connection_parameter)
db = db_client.Ohminator

# Contains all events in the event loop and all event handling
events = events.Events(client, db)

# Reads token
with open("token.txt", 'r') as f:
    token = f.read().strip()

# Starts the execution of the bot
client.run(token)
