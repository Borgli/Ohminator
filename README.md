# Ohminator, a Discord bot

The bot uses [discord.py](https://github.com/Rapptz/discord.py), an API wrapper for Discord written in Python. Currently, the bot is based on the async branch, but will probably be migrated over to the rewrite branch in the future. 

Documentation can be found [here](https://discordpy.readthedocs.io/en/latest/).

## How to install:
1. Make sure you have installed [python3.5+](https://www.python.org/).
2. Download or clone the repository.
3. Install the following dependencies:
  * `python3 -m pip install -U discord.py[voice]`
  * `python3 -m pip install -U youtube-dl`
  * `python3 -m pip install -U aiohttp`
  * `python3 -m pip install -U rocket-snake`
  * `python3 -m pip install -U gtts`
  * `python3 -m pip install -U pymongo`
4. Download [steamapi](https://github.com/smiley/steamapi) and follow the install instructions in that repository.
5. Install [FFmpeg](https://www.ffmpeg.org/) for audio:
  * `sudo apt-get install ffmpeg`
6. Create token.txt containing only the bot-token aquired from [discordapp](https://discordapp.com/developers/applications/me).

## How to register new commands (python 3.5+):
1. Create an asynchronous function using keywords `async def`. Remember to use `await` for all *coroutine* function calls only.

Example:
```python
async def roll(message, bot_channel, client):
    await client.delete_message(message)
    try:
        options = message.content.split()
        rand = randint(int(options[1]), int(options[2]))
        await client.send_message(bot_channel, '{}: You rolled {}!'.format(message.author.name, rand))
    except:
        await client.send_message(bot_channel,
                                  '{}: USAGE: !roll [lowest] [highest]'.format(message.author.name))
```
2. Register function in file [Events.py](Events.py) using the `commands` dictionary. The key should be the command string and value should be the function object.

Example:
```python
commands["!roll"] = roll
```
