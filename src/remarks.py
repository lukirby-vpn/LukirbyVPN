import json
import re
from pathlib import Path

from geoip import get_flag_emoji, translate_country


SERVERS_DIR = Path(__file__).resolve().parent.parent / "servers"

_REMARK_PATTERN = re.compile(r"^(?P<flag>\S+)\s+(?P<country>.+?)\s+#(?P<number>\d+)$")


def _get_existing_numbers(country_code: str, country: str) -> list[int]:
    """
    Find numbers already used for the specified country
    in existing generated server JSON files.
    """
    numbers = []

    if not SERVERS_DIR.exists():
        return numbers

    country_code = (country_code or "").upper()
    country = country or "Неизвестная страна"

    for file_path in SERVERS_DIR.glob("NewGeneratedServer*.json"):
        try:
            with file_path.open("r", encoding="utf-8") as file:
                config = json.load(file)

            remark = config.get("remarks")

            if not isinstance(remark, str):
                continue

            match = _REMARK_PATTERN.match(remark.strip())

            if not match:
                continue

            existing_country = match.group("country").strip()
            number = int(match.group("number"))

            # Compare by translated country name.
            # This also works with old configs that don't store countryCode.
            if existing_country == country:
                numbers.append(number)

        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            # A broken/invalid old config must not break the whole scanner.
            continue

    return numbers


def get_next_country_number(country_code: str, country: str) -> int:
    """
    Return the next persistent server number for a country.
    """
    existing_numbers = _get_existing_numbers(
        country_code=country_code,
        country=country,
    )

    if not existing_numbers:
        return 1

    return max(existing_numbers) + 1


def generate_remark(country: str | None, countryCode: str | None) -> str:
    """
    Generate a remark such as:

        🇳🇱 Нидерланды #1

    or, when GeoIP information is unavailable:

        🇫🇲 Неизвестная страна #1
    """

    if not countryCode or len(countryCode) != 2:
        countryCode = None
        country = "Неизвестная страна"

    if countryCode and not countryCode.isalpha():
        countryCode = None
        country = "Неизвестная страна"

    if not country:
        country = "Неизвестная страна"

    if countryCode:
        countryCode = countryCode.upper()
        ru_name = translate_country(country, countryCode)
        flag = get_flag_emoji(countryCode)

        # get_flag_emoji() should return 🇫🇲 only for invalid codes.
        if flag == "🇫🇲":
            countryCode = None
            ru_name = "Неизвестная страна"
            flag = "🇫🇲"
    else:
        ru_name = "Неизвестная страна"
        flag = "🇫🇲"

    number = get_next_country_number(
        country_code=countryCode or "XX",
        country=ru_name,
    )

    return f"{flag} {ru_name} #{number}"
