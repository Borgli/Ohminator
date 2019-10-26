import discord


def main():
    client = Ohminator()

    # Reads token
    with open("token.txt", 'r') as f:
        token = f.read().strip()

    # Starts the execution of the bot
    client.run(token)


if __name__ == '__main__':
    main()


class Ohminator(discord.Client):
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print(discord.version_info)
        print(discord.__version__)
        print('------')
        global running
        if not running:
            # Load database
			load_database()
            print('Done!')
            running = True

    async def on_message(self, message):
        if message.content.strip():
            commands = get_enabled_commands()
            prefix = get_prefix()
            # Normal commands can be awaited and are therefore in their own functions
            for key in commands:
                if message.content.lower().split()[0] == prefix + key:
                    await commands[key](message, get_command_details(), client)
                    return
