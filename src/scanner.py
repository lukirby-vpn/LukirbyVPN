import base64
import re
from typing import Iterable

import requests


SUPPORTED_PROTOCOLS = {
    "vless",
    "vmess",
    "trojan",
    "ss",
}

URI_REGEX = re.compile(
    r"(?P<uri>"
    r"(?:vless|vmess|trojan|ss)://"
    r"[^\s\"'<>]+"
    r")",
    re.IGNORECASE,
)

MAX_SOURCE_SIZE = 10 * 1024 * 1024  # 10 MB
REQUEST_TIMEOUT = (10, 20)

HEADERS = {
    "User-Agent": (
        "VPN-Key-Scanner/1.0 "
        "(public configuration scanner)"
    )
}


def _decode_base64(text: str) -> str | None:
    """
    Try standard Base64 and URL-safe Base64 decoding.
    Returns decoded UTF-8 text or None.
    """
    text = text.strip()

    if not text:
        return None

    # Remove whitespace commonly found in subscription files.
    compact = re.sub(r"\s+", "", text)

    # Base64 strings should have a reasonable length.
    if len(compact) < 8:
        return None

    padding = "=" * (-len(compact) % 4)

    for decoder in (base64.b64decode, base64.urlsafe_b64decode):
        try:
            decoded = decoder(compact + padding)
            result = decoded.decode("utf-8", errors="strict")

            if "://" in result:
                return result

        except (ValueError, UnicodeDecodeError):
            continue

    return None


def _extract_uris(text: str) -> set[str]:
    """
    Extract only supported VPN URI schemes.
    """
    found = set()

    for match in URI_REGEX.finditer(text):
        uri = match.group("uri").strip()

        # Remove common trailing punctuation.
        uri = uri.rstrip(".,;)]}>")

        if "://" not in uri:
            continue

        protocol = uri.split("://", 1)[0].lower()

        if protocol not in SUPPORTED_PROTOCOLS:
            continue

        found.add(uri)

    return found


def _process_content(content: str) -> set[str]:
    """
    Extract URIs from plain text or Base64 subscription content.
    """
    uris = _extract_uris(content)

    if uris:
        return uris

    decoded = _decode_base64(content)

    if decoded:
        return _extract_uris(decoded)

    return set()


def _fetch_source(session: requests.Session, source: str) -> str | None:
    """
    Download one source with size protection.
    """
    try:
        response = session.get(
            source,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            stream=True,
        )

        response.raise_for_status()

        content_length = response.headers.get("Content-Length")

        if content_length:
            try:
                if int(content_length) > MAX_SOURCE_SIZE:
                    print(
                        f"[SKIP] Source too large: {source}"
                    )
                    return None
            except ValueError:
                pass

        chunks = []
        total_size = 0

        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue

            total_size += len(chunk)

            if total_size > MAX_SOURCE_SIZE:
                print(
                    f"[SKIP] Source exceeded size limit: {source}"
                )
                return None

            chunks.append(chunk)

        raw = b"".join(chunks)

        return raw.decode(
            response.encoding or "utf-8",
            errors="replace",
        )

    except requests.RequestException as exc:
        print(f"[ERROR] Failed to fetch {source}: {exc}")
        return None


def fetch_and_extract_uris(
    sources: Iterable[str],
) -> list[str]:
    """
    Fetch all configured sources and return unique
    supported VPN URIs.
    """
    uris: set[str] = set()

    with requests.Session() as session:
        for source in sources:
            source = source.strip()

            if not source:
                continue

            print(f"[SCAN] {source}")

            content = _fetch_source(
                session,
                source,
            )

            if content is None:
                continue

            found = _process_content(content)

            print(
                f"[FOUND] {len(found)} supported URI(s)"
            )

            uris.update(found)

    return sorted(uris)
