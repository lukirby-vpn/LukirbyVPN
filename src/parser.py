import base64
import binascii
import json
from urllib.parse import parse_qs, unquote, urlparse


SUPPORTED_PROTOCOLS = {
    "vless",
    "vmess",
    "trojan",
    "ss",
    "shadowsocks",
}


def _first(query, key, default=""):
    values = query.get(key)

    if not values:
        return default

    return values[0]


def _decode_b64(value):
    """
    Decode standard or URL-safe Base64.
    """
    if not value:
        return None

    value = value.strip()

    # VMess/SS subscriptions sometimes contain whitespace.
    value = "".join(value.split())

    padding = "=" * (-len(value) % 4)

    decoders = (
        base64.b64decode,
        base64.urlsafe_b64decode,
    )

    for decoder in decoders:
        try:
            decoded = decoder(value + padding)

            return decoded.decode(
                "utf-8",
                errors="strict",
            )

        except (
            ValueError,
            UnicodeDecodeError,
            binascii.Error,
        ):
            continue

    return None


def _validate_endpoint(host, port):
    if not host:
        return False

    if port is None:
        return False

    try:
        port = int(port)
    except (TypeError, ValueError):
        return False

    return 1 <= port <= 65535


def parse_uri(uri):
    if not isinstance(uri, str):
        return None

    uri = uri.strip()

    if "://" not in uri:
        return None

    try:
        scheme = urlparse(uri).scheme.lower()
    except ValueError:
        return None

    if scheme not in SUPPORTED_PROTOCOLS:
        print(
            f"[!] UNSUPPORTED_PROTOCOL: "
            f"'{scheme}' detected. Skipping."
        )
        return None

    try:
        if scheme == "vless":
            return parse_vless(uri)

        if scheme == "vmess":
            return parse_vmess(uri)

        if scheme == "trojan":
            return parse_trojan(uri)

        if scheme in {"ss", "shadowsocks"}:
            return parse_ss(uri)

    except Exception as exc:
        print(
            f"[!] PARSE_ERROR: "
            f"{scheme}: {type(exc).__name__}"
        )

    return None


def parse_vless(uri):
    parsed = urlparse(uri)
    query = parse_qs(
        parsed.query,
        keep_blank_values=True,
    )

    host = parsed.hostname
    port = parsed.port

    if not _validate_endpoint(host, port):
        return None

    if not parsed.username:
        return None

    transport = _first(query, "type", "tcp").lower()
    security = _first(query, "security", "none").lower()

    return {
        "protocol": "vless",

        "uuid": unquote(parsed.username),

        "host": host,
        "port": port,

        "type": transport,
        "security": security,

        "sni": _first(query, "sni"),
        "fp": _first(query, "fp"),
        "pbk": _first(query, "pbk"),
        "sid": _first(query, "sid"),
        "flow": _first(query, "flow"),

        "path": _first(query, "path"),
        "host_header": _first(query, "host"),

        "serviceName": _first(
            query,
            "serviceName",
        ),

        "alpn": _first(query, "alpn"),

        "remark": unquote(
            parsed.fragment or ""
        ),
    }


def parse_vmess(uri):
    raw = uri[len("vmess://"):].strip()

    decoded = _decode_b64(raw)

    if not decoded:
        return None

    try:
        data = json.loads(decoded)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None

    host = data.get("add")
    uuid = data.get("id")

    try:
        port = int(data.get("port", 443))
    except (TypeError, ValueError):
        return None

    if not _validate_endpoint(host, port):
        return None

    if not uuid:
        return None

    network = str(
        data.get("net", "tcp")
    ).lower()

    tls_value = str(
        data.get("tls", "")
    ).lower()

    if tls_value in {
        "tls",
        "xtls",
    }:
        security = tls_value
    else:
        security = "none"

    return {
        "protocol": "vmess",

        "uuid": uuid,

        "host": host,
        "port": port,

        "type": network,
        "security": security,

        "sni": data.get("sni", ""),
        "fp": data.get("fp", ""),

        "path": data.get("path", ""),
        "host_header": data.get("host", ""),

        "serviceName": data.get(
            "serviceName",
            "",
        ),

        "aid": data.get(
            "aid",
            0,
        ),

        "scy": data.get(
            "scy",
            "auto",
        ),

        "alpn": data.get(
            "alpn",
            "",
        ),

        "remark": data.get(
            "ps",
            "",
        ),
    }


def parse_trojan(uri):
    parsed = urlparse(uri)

    query = parse_qs(
        parsed.query,
        keep_blank_values=True,
    )

    host = parsed.hostname
    port = parsed.port

    if not _validate_endpoint(host, port):
        return None

    if not parsed.username:
        return None

    transport = _first(
        query,
        "type",
        "tcp",
    ).lower()

    security = _first(
        query,
        "security",
        "tls",
    ).lower()

    return {
        "protocol": "trojan",

        "password": unquote(
            parsed.username
        ),

        "host": host,
        "port": port,

        "type": transport,
        "security": security,

        "sni": _first(
            query,
            "sni",
        ),

        "fp": _first(
            query,
            "fp",
        ),

        "path": _first(
            query,
            "path",
        ),

        "host_header": _first(
            query,
            "host",
        ),

        "serviceName": _first(
            query,
            "serviceName",
        ),

        "alpn": _first(
            query,
            "alpn",
        ),

        "flow": _first(
            query,
            "flow",
        ),

        "remark": unquote(
            parsed.fragment or ""
        ),
    }


def parse_ss(uri):
    parsed = urlparse(uri)

    remark = unquote(
        parsed.fragment or ""
    )

    body = uri.split(
        "://",
        1,
    )[1]

    if "#" in body:
        body = body.split(
            "#",
            1,
        )[0]

    body = body.strip()

    method = None
    password = None
    host = None
    port = None

    # Format:
    #
    # ss://BASE64(method:password)@host:port
    #
    if "@" in body:
        credentials, endpoint = body.rsplit(
            "@",
            1,
        )

        decoded_credentials = _decode_b64(
            credentials
        )

        if decoded_credentials:
            credentials = decoded_credentials

        if ":" not in credentials:
            return None

        method, password = credentials.split(
            ":",
            1,
        )

        endpoint = endpoint.strip()

        parsed_endpoint = urlparse(
            f"//{endpoint}"
        )

        host = parsed_endpoint.hostname
        port = parsed_endpoint.port

    else:
        # Legacy format:
        #
        # ss://BASE64(method:password@host:port)
        #
        decoded = _decode_b64(body)

        if not decoded or "@" not in decoded:
            return None

        credentials, endpoint = decoded.rsplit(
            "@",
            1,
        )

        if ":" not in credentials:
            return None

        method, password = credentials.split(
            ":",
            1,
        )

        parsed_endpoint = urlparse(
            f"//{endpoint}"
        )

        host = parsed_endpoint.hostname
        port = parsed_endpoint.port

    if not method or password is None:
        return None

    if not _validate_endpoint(host, port):
        return None

    return {
        "protocol": "shadowsocks",

        "method": method,
        "password": password,

        "host": host,
        "port": port,

        "remark": remark,
      }
