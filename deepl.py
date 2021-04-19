import datetime
from enum import Enum
from typing import Optional, List, Any

import requests

from settings import AppSettings


class DeeplApiLanguage(Enum):
	Bulgarian = 'BG'
	Czech = 'CS'
	Danish = 'DA'
	German = 'DE'
	Greek = 'EL'
	English = 'EN'
	Spanish = 'ES'
	Estonian = 'ET'
	Finnish = 'FI'
	French = 'FR'
	Hungarian = 'HU'
	Italian = 'IT'
	Japanese = 'JA'
	Lithuanian = 'LT'
	Latvian = 'LV'
	Dutch = 'NL'
	Polish = 'PL'
	Portuguese = 'PT'
	Romanian = 'RO'
	Russian = 'RU'
	Slovak = 'SK'
	Slovenian = 'SL'
	Swedish = 'SV'
	Chinese = 'ZH'


class DeeplApi:
	_REQUEST_TIMEOUT: int = 10
	_BASE_API: str = 'https://api-free.deepl.com/v2/translate'

	_token: str

	def __init__(self, token: str):
		self._token = token

	def translate(
			self,
			text: str,
			target_language: DeeplApiLanguage = DeeplApiLanguage.English,
			source_language: Optional[DeeplApiLanguage] = None
	) -> str:
		response: requests.Response = requests.post(
			url=type(self)._BASE_API,
			params=dict(
				auth_key=self._token
			),
			data=dict(
				text=text,
				target_lang=target_language.value
			),
			timeout=type(self)._REQUEST_TIMEOUT
		)
		response.raise_for_status()

		translations: list[dict[str, str]] = response.json()['translations']
		translated_text: str = '\n'.join(translation['text'] for translation in translations)

		return translated_text


if __name__ == '__main__':
	settings: AppSettings = AppSettings.from_file()
	translator: DeeplApi = DeeplApi(settings.deepl_token)

	while True:
		raw_text: str = input('>')
		raw_text = raw_text.strip()

		if not raw_text:
			break

		translated_text: str = translator.translate(raw_text, DeeplApiLanguage.English)
		print(translated_text)
