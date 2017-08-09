import discord
import asyncio

import pymongo

import Events
import pickle
from os.path import exists

client = discord.Client()

db_client = pymongo.MongoClient("mongodb://Ohminator:an4MgtGkIlgOLo0h@ohminator-cluster-shard-00-00-it3lf.mongodb.net:27017,ohminator-cluster-shard-00-01-it3lf.mongodb.net:27017,ohminator-cluster-shard-00-02-it3lf.mongodb.net:27017/Ohminator?ssl=true&replicaSet=Ohminator-cluster-shard-0&authSource=admin")
db = db_client.Ohminator

# Contains all events in the event loop and all event handling
events = Events.Events(client, db)

# Reads token
with open("token.txt", 'r') as f:
    token = f.read().strip()

# Starts the execution of the bot
client.run(token)

