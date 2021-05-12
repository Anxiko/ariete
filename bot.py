from dataclasses import dataclass
from typing import Optional, Union, Callable, Coroutine, Iterable, AsyncIterable

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

	raise ArgumentParsingError(f"Could not parse {raw_argument} as a language or member")


async def _parse_translate_arguments(context: Context, arguments: tuple[str]) -> TranslateArguments:
	if len(arguments) > 3:
		raise TooManyArguments(f"Command only takes a maximum of 3 arguments, but {len(arguments)} were given.")

	parsed_arguments: list[Union[DeeplApiLanguage, discord.Member]] = [
		await _parse_translate_argument(context, argument) for argument in arguments
	]

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

	# If there's a member, it has to be either at the beginning or at the end of the argument list
	if len(members) == 1 and len(parsed_arguments) == 3 and isinstance(parsed_arguments[1], discord.Member):
		raise BadArgument(f"Member arguments must be present at the beginning or end of the list of arguments.")

	target_language: Optional[DeeplApiLanguage]
	source_language: Optional[DeeplApiLanguage]

	if len(languages) == 2:
		# When given two languages, first is source, and second is target
		source_language, target_language = languages

		if source_language == target_language:
			raise BadArgument("Target and source languages can't be the same.")
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

	if translate_arguments.target_member == bot.user:
		raise BadArgument(f"Can't translate messages sent by the bot.")

	target_message: discord.Message

	invocation_message: discord.Message = context.message
	if invocation_message.reference is not None:
		# If this message is a reply, the text to translate is the text replied to
		target_message = invocation_message.reference.resolved  # TODO: this has a chance at failing, handle possible exception?
		if not isinstance(target_message, discord.Message):
			raise commands.CommandError("Could not extract message from reply")
		if translate_arguments.target_member is not None:
			raise BadArgument("Target member shouldn't be specified on replies")
	else:
		# If the invocation isn't a reply, fetch the first valid message from the channel to translate

		"""
		There doesn't seem to be a good way to get a member's history within a channel.
		It would seem that a member's history() method should do it, but this history corresponds to DMs, not to the channel.
		"""
		message_in_history: discord.Message
		async for message_in_history in context.history(limit=_MESSAGE_HISTORY_LIMIT):
			if (
					message_in_history.author != bot.user  # Ignore messages sent by this bot
					and
					context.message != message_in_history  # Ignore the message that triggered this invocation
					and
					# Just to be safe, ignore all commands that start with the command prefix
					# TODO: could this check be less broad?
					(not message_in_history.content.startswith(_COMMAND_PREFIX))
					and
					# Ignore if message author does not match specified target member (if any were given)
					(
							translate_arguments.target_member is None
							or
							translate_arguments.target_member == message_in_history.author
					)
			):
				target_message = message_in_history
				break
		else:
			raise commands.BadArgument("Found no message to translate.")

	translated_text: str = translator.translate(
		target_message.content,
		target_language=translate_arguments.target_language,
		source_language=translate_arguments.source_language
	)

	await target_message.reply(translated_text)


@translate.error
async def translate_error_handler(context: commands.Context, error: commands.CommandError) -> None:
	if isinstance(error, commands.UserInputError):
		await context.send(f"User error:\n```{error}```")
	else:
		await context.send(f"Unknown error.")  # TODO: log errors


if __name__ == '__main__':
	bot.run(settings.discord_token)
