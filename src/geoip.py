import requests

COUNTRY_TRANSLATIONS = {
    "US": "США",
    "NL": "Нидерланды",
    "DE": "Германия",
    "GB": "Великобритания",
    "FR": "Франция",
    "PL": "Польша",
    "RU": "Россия",
    "UA": "Украина",
    "FI": "Финляндия",
    "SE": "Швеция",
    "TR": "Турция",
    "SG": "Сингапур",
    "JP": "Япония",
    "CN": "Китай",
    "IN": "Индия",
    "BR": "Бразилия",
    "CA": "Канада",
    "AU": "Австралия",
    "IT": "Италия",
    "ES": "Испания",
    "CH": "Швейцария",
    "AT": "Австрия",
    "CZ": "Чехия",
    "RO": "Румыния",
    "BG": "Болгария",
    "HK": "Гонконг",
    "KR": "Южная Корея",
    "KZ": "Казахстан",
}


def translate_country(country, country_code):
    if not country_code:
        return "Неизвестная страна"

    country_code = country_code.upper()

    return COUNTRY_TRANSLATIONS.get(
        country_code,
        country or "Неизвестная страна"
    )


def get_flag_emoji(country_code):
    if not country_code or len(country_code) != 2:
        return "🇫🇲"

    country_code = country_code.upper()

    if not country_code.isalpha():
        return "🇫🇲"

    return "".join(
        chr(ord(char) + 127397)
        for char in country_code
    )


def get_geoip(ip, timeout=10):
    """
    Get country information for an IP address.
    """
    if not ip:
        return None

    url = f"https://ip-api.com/json/{ip}"

    params = {
        "fields": "status,country,countryCode,query"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=timeout
        )

        response.raise_for_status()
        data = response.json()

        if data.get("status") != "success":
            return None

        country_code = data.get("countryCode")
        country = translate_country(
            data.get("country"),
            country_code
        )

        flag = get_flag_emoji(country_code)

        return {
            "ip": data.get("query", ip),
            "country": country,
            "countryCode": country_code,
            "flag": flag
        }

    except (requests.RequestException, ValueError):
        return None
