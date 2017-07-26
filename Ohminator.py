import discord
import asyncio
import Events
import pickle
from os.path import exists

client = discord.Client()

# Contains all events in the event loop and all event handling
events = Events.Events(client)

# Reads token
with open("token.txt", 'r') as f:
    token = f.read()

# Starts the execution of the bot
client.run(token)
