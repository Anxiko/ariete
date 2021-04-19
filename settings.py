import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATA_FOLDER: Path = Path('.data')
SETTINGS_FILENAME: str = 'settings.json'


@dataclass
class AppSettings:
	discord_token: str
	deepl_token: str

	@classmethod
	def from_file(cls) -> 'AppSettings':
		with open(DATA_FOLDER / SETTINGS_FILENAME) as f:
			parsed_json: dict[str, Any] = json.load(f)
			return cls(**parsed_json)
