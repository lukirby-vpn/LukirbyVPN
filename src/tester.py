import json
import os
import socket
import subprocess
import tempfile
import time

import requests


YOUTUBE_URLS = (
    "https://www.youtube.com/",
    "https://www.youtube.com/generate_204",
)

IP_CHECK_URL = "https://ip-api.com/json/?fields=status,query,country,countryCode"

STARTUP_TIMEOUT = 8
REQUEST_TIMEOUT = 10
MAX_YOUTUBE_BYTES = 64 * 1024

MAX_LATENCY_MS = 500


def _wait_for_port(host, port, timeout):
    """
    Wait until local Xray SOCKS port becomes available.
    """
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        try:
            with socket.create_connection(
                (host, port),
                timeout=0.5,
            ):
                return True
        except OSError:
            time.sleep(0.1)

    return False


def _terminate_process(process):
    if process is None:
        return

    try:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        try:
            process.kill()
            process.wait(timeout=2)
        except Exception:
            pass
    except Exception:
        pass


def _check_youtube(session, proxies):
    """
    Verify that YouTube can actually be reached through
    the tested proxy.

    We don't download the entire page.
    """
    for url in YOUTUBE_URLS:
        try:
            response = session.get(
                url,
                proxies=proxies,
                timeout=REQUEST_TIMEOUT,
                stream=True,
                allow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(X11; Linux x86_64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/120 Safari/537.36"
                    )
                },
            )

            if response.status_code != 200:
                response.close()
                continue

            received = 0

            for chunk in response.iter_content(
                chunk_size=8192
            ):
                if not chunk:
                    continue

                received += len(chunk)

                if received >= MAX_YOUTUBE_BYTES:
                    break

            response.close()

            if received > 0:
                return True

        except requests.RequestException:
            continue

    return False


def _measure_latency(session, proxies):
    """
    Measure proxy request latency in milliseconds.
    """
    start = time.monotonic()

    try:
        response = session.get(
            "https://www.youtube.com/generate_204",
            proxies=proxies,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False,
        )

        response.close()

        elapsed = (
            time.monotonic() - start
        ) * 1000

        return int(elapsed)

    except requests.RequestException:
        return None


def test_server(
    temp_xray_config,
    local_port,
):
    """
    Test an Xray configuration.

    A server is WORKING only when:

    1. Xray starts successfully.
    2. SOCKS5 becomes available.
    3. External IP can be obtained through the proxy.
    4. YouTube actually responds through the proxy.
    5. Latency is <= 500 ms.
    """

    result = {
        "status": "FAILED",
        "ip": None,
        "country": None,
        "countryCode": None,
        "latency": None,
        "youtube": False,
        "reason": None,
    }

    temp_file = None
    process = None

    try:
        # Create temporary config outside the repository.
        fd, temp_file = tempfile.mkstemp(
            prefix="xray_test_",
            suffix=".json",
        )

        os.close(fd)

        with open(
            temp_file,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                temp_xray_config,
                file,
                ensure_ascii=False,
                indent=2,
            )

        xray_executable = (
            "./xray"
            if os.name != "nt"
            else "xray.exe"
        )

        if not os.path.isfile(
            xray_executable
        ):
            result["reason"] = (
                "Xray executable not found"
            )
            return result

        process = subprocess.Popen(
            [
                xray_executable,
                "run",
                "-test",
                "-config",
                temp_file,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Xray -test validates config and exits.
        # If it exits immediately, the config is invalid.
        time.sleep(0.5)

        if process.poll() is not None:
            result["reason"] = (
                "Xray config validation failed"
            )
            return result

        if not _wait_for_port(
            "127.0.0.1",
            local_port,
            STARTUP_TIMEOUT,
        ):
            result["reason"] = (
                "SOCKS5 port did not open"
            )
            return result

        proxies = {
            "http": (
                f"socks5h://127.0.0.1:"
                f"{local_port}"
            ),
            "https": (
                f"socks5h://127.0.0.1:"
                f"{local_port}"
            ),
        }

        with requests.Session() as session:

            # --------------------------------------
            # External IP / GeoIP
            # --------------------------------------

            try:
                ip_response = session.get(
                    IP_CHECK_URL,
                    proxies=proxies,
                    timeout=REQUEST_TIMEOUT,
                )

                ip_response.raise_for_status()

                ip_data = ip_response.json()

            except (
                requests.RequestException,
                ValueError,
            ):
                result["reason"] = (
                    "Proxy cannot reach IP API"
                )
                return result

            if ip_data.get("status") != "success":
                result["reason"] = (
                    "IP API failed"
                )
                return result

            vpn_ip = ip_data.get("query")

            if not vpn_ip:
                result["reason"] = (
                    "No external IP returned"
                )
                return result

            result["ip"] = vpn_ip
            result["country"] = ip_data.get(
                "country"
            )
            result["countryCode"] = ip_data.get(
                "countryCode"
            )

            # --------------------------------------
            # YouTube
            # --------------------------------------

            youtube_ok = _check_youtube(
                session,
                proxies,
            )

            result["youtube"] = youtube_ok

            if not youtube_ok:
                result["reason"] = (
                    "YouTube unavailable through VPN"
                )
                return result

            # --------------------------------------
            # Latency
            # --------------------------------------

            latency = _measure_latency(
                session,
                proxies,
            )

            if latency is None:
                result["reason"] = (
                    "Latency test failed"
                )
                return result

            result["latency"] = latency

            if latency > MAX_LATENCY_MS:
                result["reason"] = (
                    f"Latency too high: "
                    f"{latency} ms"
                )
                return result

            # --------------------------------------
            # SUCCESS
            # --------------------------------------

            result["status"] = "WORKING"
            result["reason"] = None

            return result

    except Exception as exc:
        result["reason"] = (
            f"{type(exc).__name__}: {exc}"
        )

        return result

    finally:
        _terminate_process(process)

        if temp_file:
            try:
                os.remove(temp_file)
            except OSError:
                pass
