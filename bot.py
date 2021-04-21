from dataclasses import dataclass
from typing import Optional, Union

import discord
from discord.ext import commands
from discord.ext.commands import MemberConverter, Context, TooManyArguments, ArgumentParsingError, BadArgument

from deepl import DeeplApi, DeeplApiLanguage
from settings import AppSettings

_MESSAGE_HISTORY_LIMIT: int = 100

_COMMAND_PREFIX: str = '!'

settings: AppSettings = AppSettings.from_file()
translator: DeeplApi = DeeplApi(settings.deepl_token)
bot: commands.Bot = commands.Bot(command_prefix=_COMMAND_PREFIX)


@bot.command()
async def ping(context: commands.Context) -> None:
	await context.send('Pong')


@dataclass
class TranslateArguments:
	source_language: Optional[DeeplApiLanguage]
	target_language: DeeplApiLanguage
	target_member: Optional[discord.Member]


async def _parse_translate_argument(
		context: Context, raw_argument: str) -> Optional[Union[DeeplApiLanguage, discord.Member]]:
	raw_argument = raw_argument.upper()

	try:
		return DeeplApiLanguage(raw_argument)
	except ValueError:
		pass

	try:
		converter: MemberConverter = MemberConverter()
		member: discord.Member = await converter.convert(context, raw_argument)

		return member
	except Exception as e:
		print(f"{e!r}")

	return None


async def _parse_translate_arguments(context: Context, arguments: tuple[str]) -> TranslateArguments:
	if len(arguments) > 3:
		raise TooManyArguments(f"Command only takes a maximum of 3 arguments, but {len(arguments)} were given.")

	parsed_arguments: list[Optional[Union[DeeplApiLanguage, discord.Member]]] = []
	for argument in arguments:
		parsed_argument: Optional[Union[DeeplApiLanguage, discord.Member]] = await _parse_translate_argument(
			context, argument
		)

		if parsed_argument is None:
			raise ArgumentParsingError(f"Could not parse {argument} as a language or member")
		parsed_arguments.append(parsed_argument)

	# If there's a member,
	if len(parsed_arguments) == 3 and isinstance(parsed_arguments[1], discord.Member):
		raise BadArgument(f"Member arguments must be present at the beginning or end of the list of arguments.")

	languages: list[DeeplApiLanguage] = []
	members: list[discord.Member] = []

	for parsed_argument in parsed_arguments:
		if isinstance(parsed_argument, DeeplApiLanguage):
			languages.append(parsed_argument)
		else:
			members.append(parsed_argument)

	if len(members) > 1:
		raise BadArgument(f"Only 1 member can be given as an argument.")
	if len(languages) > 2:
		raise BadArgument(f"A maximum of 2 languages can be given as arguments.")

	target_language: Optional[DeeplApiLanguage]
	source_language: Optional[DeeplApiLanguage]

	if len(languages) == 2:
		# When given two languages, first is source, and second is target
		source_language, target_language = languages
	elif len(languages) == 1:
		# If only one language is present, it has to be the target, since the source can be guessed
		source_language, target_language = None, languages[0]
	else:
		# With no languages given, we'll assume english for the target, and guess the source
		source_language, target_language = None, DeeplApiLanguage.English

	return TranslateArguments(
		source_language=source_language,
		target_language=target_language,
		target_member=members[0] if len(members) > 0 else None
	)


@bot.command()
async def translate(context: commands.Context, *args: str) -> None:
	translate_arguments: TranslateArguments = await _parse_translate_arguments(context, args)

	message: discord.Message
	async for message in context.history(limit=_MESSAGE_HISTORY_LIMIT):
		if message.author == bot.user or context.message == message:
			continue
		if translate_arguments.target_member is not None and translate_arguments.target_member != message.author:
			continue  # TODO: get history directly from member, when target member is specified
		if message.content.startswith(_COMMAND_PREFIX):
			continue

		translated_text: str = translator.translate(
			message.content,
			target_language=translate_arguments.target_language,
			source_language=translate_arguments.source_language
		)
		await context.send(translated_text)
		break
	else:
		await context.send("Found no message to translate")


if __name__ == '__main__':
	bot.run(settings.discord_token)
