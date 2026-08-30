import json


SUPPORTED_PROTOCOLS = {
    "vless",
    "vmess",
    "trojan",
    "shadowsocks",
}


def _require(parsed, *fields):
    for field in fields:
        value = parsed.get(field)

        if value is None or value == "":
            raise ValueError(
                f"Missing required field: {field}"
            )


def _base_inbound(local_port):
    return {
        "tag": "socks",
        "port": int(local_port),
        "listen": "127.0.0.1",
        "protocol": "socks",
        "settings": {
            "udp": True,
            "auth": "noauth",
        },
        "sniffing": {
            "enabled": True,
            "routeOnly": False,
            "destOverride": [
                "http",
                "tls",
                "quic",
            ],
        },
    }


def _build_vless(parsed):
    _require(
        parsed,
        "host",
        "port",
        "uuid",
    )

    user = {
        "id": parsed["uuid"],
        "encryption": "none",
    }

    if parsed.get("flow"):
        user["flow"] = parsed["flow"]

    return {
        "protocol": "vless",
        "settings": {
            "vnext": [
                {
                    "address": parsed["host"],
                    "port": int(parsed["port"]),
                    "users": [user],
                }
            ]
        },
    }


def _build_vmess(parsed):
    _require(
        parsed,
        "host",
        "port",
        "uuid",
    )

    user = {
        "id": parsed["uuid"],
        "alterId": int(
            parsed.get("aid", 0) or 0
        ),
        "security": parsed.get(
            "scy",
            "auto",
        ),
    }

    return {
        "protocol": "vmess",
        "settings": {
            "vnext": [
                {
                    "address": parsed["host"],
                    "port": int(parsed["port"]),
                    "users": [user],
                }
            ]
        },
    }


def _build_trojan(parsed):
    _require(
        parsed,
        "host",
        "port",
        "password",
    )

    server = {
        "address": parsed["host"],
        "port": int(parsed["port"]),
        "password": parsed["password"],
    }

    if parsed.get("flow"):
        server["flow"] = parsed["flow"]

    return {
        "protocol": "trojan",
        "settings": {
            "servers": [server],
        },
    }


def _build_shadowsocks(parsed):
    _require(
        parsed,
        "host",
        "port",
        "method",
        "password",
    )

    return {
        "protocol": "shadowsocks",
        "settings": {
            "servers": [
                {
                    "address": parsed["host"],
                    "port": int(parsed["port"]),
                    "method": parsed["method"],
                    "password": parsed["password"],
                }
            ]
        },
    }


def _apply_security(outbound, parsed):
    security = (
        parsed.get("security", "none")
        or "none"
    ).lower()

    if security == "none":
        outbound["streamSettings"]["security"] = "none"
        return

    if security == "tls":
        tls_settings = {}

        sni = parsed.get("sni")

        if sni:
            tls_settings["serverName"] = sni

        fp = parsed.get("fp")

        if fp:
            tls_settings["fingerprint"] = fp

        outbound["streamSettings"][
            "security"
        ] = "tls"

        outbound["streamSettings"][
            "tlsSettings"
        ] = tls_settings

        return

    if security == "reality":
        _require(
            parsed,
            "pbk",
            "sid",
        )

        reality = {
            "publicKey": parsed["pbk"],
            "shortId": parsed["sid"],
        }

        sni = parsed.get("sni")

        if sni:
            reality["serverName"] = sni

        fp = parsed.get("fp")

        if fp:
            reality["fingerprint"] = fp

        outbound["streamSettings"][
            "security"
        ] = "reality"

        outbound["streamSettings"][
            "realitySettings"
        ] = reality

        return

    raise ValueError(
        f"Unsupported security: {security}"
    )


def _apply_transport(outbound, parsed):
    network = (
        parsed.get("type", "tcp")
        or "tcp"
    ).lower()

    stream = outbound.setdefault(
        "streamSettings",
        {},
    )

    stream["network"] = network

    if network == "tcp":
        return

    if network == "ws":
        ws_settings = {
            "path": parsed.get(
                "path",
                "/",
            ) or "/",
        }

        host = parsed.get(
            "host_header"
        )

        if host:
            ws_settings["headers"] = {
                "Host": host
            }

        stream["wsSettings"] = ws_settings
        return

    if network == "grpc":
        grpc_settings = {}

        service_name = parsed.get(
            "serviceName"
        )

        if service_name:
            grpc_settings[
                "serviceName"
            ] = service_name

        stream["grpcSettings"] = grpc_settings
        return

    raise ValueError(
        f"Unsupported transport: {network}"
    )


def generate_xray_json(
    parsed,
    is_temp=False,
    local_port=1080,
    remark=None,
):
    """
    Convert a parsed public VPN URI into an
    Xray-compatible outbound configuration.

    The function does not use a universal protocol
    template. Each protocol has its own builder.
    """

    if not isinstance(parsed, dict):
        raise ValueError(
            "parsed must be a dictionary"
        )

    protocol = (
        parsed.get("protocol", "")
        .lower()
    )

    if protocol not in SUPPORTED_PROTOCOLS:
        raise ValueError(
            f"Unsupported protocol: {protocol}"
        )

    if protocol == "vless":
        outbound = _build_vless(parsed)

    elif protocol == "vmess":
        outbound = _build_vmess(parsed)

    elif protocol == "trojan":
        outbound = _build_trojan(parsed)

    elif protocol == "shadowsocks":
        outbound = _build_shadowsocks(parsed)

    else:
        raise ValueError(
            f"Unsupported protocol: {protocol}"
        )

    # Shadowsocks can have transports in some
    # configurations, but only apply transport
    # information when the parser explicitly supplied it.
    if (
        protocol != "shadowsocks"
        or parsed.get("type")
    ):
        _apply_transport(
            outbound,
            parsed,
        )

    _apply_security(
        outbound,
        parsed,
    )

    config = {
        "log": {
            "loglevel": "warning"
        },

        "inbounds": [
            _base_inbound(local_port)
        ],

        "outbounds": [
            {
                **outbound,
                "tag": "proxy",
            },
            {
                "tag": "direct",
                "protocol": "freedom",
            },
            {
                "tag": "block",
                "protocol": "blackhole",
            },
        ],

        "routing": {
            "domainStrategy": "AsIs",
            "rules": [
                {
                    "type": "field",
                    "ip": [
                        "geoip:private"
                    ],
                    "outboundTag": "direct",
                }
            ],
        },
    }

    # Temporary configs are used only for testing.
    # Permanent configs receive the GeoIP-generated remark.
    if not is_temp:
        final_remark = (
            remark
            or parsed.get("generated_remark")
            or parsed.get("remark")
        )

        if final_remark:
            config["remarks"] = final_remark

    return config


def validate_xray_json(config):
    """
    Basic structural validation before writing
    the configuration to disk.
    """

    if not isinstance(config, dict):
        return False

    if not isinstance(
        config.get("inbounds"),
        list,
    ):
        return False

    if not isinstance(
        config.get("outbounds"),
        list,
    ):
        return False

    for outbound in config["outbounds"]:
        if not isinstance(outbound, dict):
            return False

        if "protocol" not in outbound:
            return False

    return True


def dumps_xray_json(config):
    """
    Serialize configuration with readable formatting.
    """
    if not validate_xray_json(config):
        raise ValueError(
            "Invalid Xray configuration"
        )

    return json.dumps(
        config,
        ensure_ascii=False,
        indent=2,
  )
