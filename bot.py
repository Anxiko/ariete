import discord
from discord.ext import commands

from deepl import DeeplApi
from settings import AppSettings

_MESSAGE_HISTORY_LIMIT: int = 100

settings: AppSettings = AppSettings.from_file()
translator: DeeplApi = DeeplApi(settings.deepl_token)
bot: commands.Bot = commands.Bot(command_prefix='!')


@bot.command()
async def ping(context: commands.Context) -> None:
	await context.send('Pong')


@bot.command()
async def translate(context: commands.Context) -> None:
	message: discord.Message
	async for message in context.history(limit=_MESSAGE_HISTORY_LIMIT):
		if message.author == bot.user or context.message == message:
			continue
		translated_text: str = translator.translate(message.content)
		await context.send(translated_text)
		break
	else:
		await context.send("Found no message to translate")


if __name__ == '__main__':
	bot.run(settings.discord_token)
