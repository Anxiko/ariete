from discord.ext import commands

from settings import AppSettings

bot: commands.Bot = commands.Bot(command_prefix='!')


@bot.command()
async def ping(context: commands.Context) -> None:
	await context.send('Pong')


@bot.command()
async def translate(context: commands.Context) -> None:
	pass


def main() -> None:
	settings: AppSettings = AppSettings.from_file()

	bot.run(settings.discord_token)


if __name__ == '__main__':
	main()
