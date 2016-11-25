import discord
import asyncio
import Events
import pickle
from os.path import exists

client = discord.Client()

# Contains all events in the event loop and all event handling
events = Events.Events(client)

# Starts the execution of the bot
client.run('MTc2NDMzMTMwMzM1NTAyMzM3.CgvoFg.FLaupAZZ5OviZ1Fb7gAO_Aq-sLo')