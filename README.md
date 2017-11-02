# Ohminator, a Discord bot

## How to install:
1. Download or clone the repository.
2. Install the following dependencies:
  * `python3 -m pip install -U discord.py[voice]`
  * `python3 -m pip install -U youtube-dl`
  * `python3 -m pip install -U aiohttp`
  * `python3 -m pip install -U rocket-snake`
  * `python3 -m pip install -U gtts`
  * `python3 -m pip install -U pymongo`
3. Download [steamapi](https://github.com/smiley/steamapi) and follow the install instructions in that repository.
4. Install FFMPEG for audio:
  * `sudo apt-get install ffmpeg`
5. Create token.txt containing only the bot-token aquired from [discordapp](https://discordapp.com/developers/applications/me).

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
