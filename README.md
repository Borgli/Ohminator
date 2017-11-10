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
  * `python3 -m pip install -U python-dateutil`
4. Download [steamapi](https://github.com/smiley/steamapi) and follow the install instructions in that repository.
5. Install [FFmpeg](https://www.ffmpeg.org/) for audio:
  * `sudo apt-get install ffmpeg`
6. Create token.txt containing only the bot-token aquired from [discordapp](https://discordapp.com/developers/applications/me).

## How to register new commands (python 3.5+):
1. Create an asynchronous function using keywords `async def`. Remember to use `await` for all *coroutine* function calls only.

Example:
```python
@register_command("roll")
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
2. Register function by using decorator `@register_command("command name one", "command name two", ect)`. Command prefix (like '!') must be omitted as this is added automatically. `register_command` is found in the `utils` module. Use `from utils import register_command` to access it.

Example:
```python
@register_command("ping")
async def ping(message, bot_channel, client):
    await client.delete_message(message)
    await client.send_message(bot_channel, 'Pong!')
```
