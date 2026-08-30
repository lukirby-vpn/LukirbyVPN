import concurrent.futures
import json
import os
import threading

from scanner import fetch_and_extract_uris
from parser import parse_uri
from tester import test_server
from converter import generate_xray_json
from utils import generate_fingerprint, log_result
from remarks import generate_remark


KNOWN_SERVERS_FILE = "data/known_servers.json"
SERVERS_DIR = "servers"

MAX_WORKERS = 5
BASE_TEST_PORT = 10000


def load_known_servers():
    if not os.path.exists(KNOWN_SERVERS_FILE):
        return set()

    try:
        with open(
            KNOWN_SERVERS_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, list):
            return set()

        return set(
            item
            for item in data
            if isinstance(item, str)
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return set()


def save_known_servers(known_servers):
    os.makedirs(
        os.path.dirname(KNOWN_SERVERS_FILE),
        exist_ok=True,
    )

    temp_file = (
        f"{KNOWN_SERVERS_FILE}.tmp"
    )

    with open(
        temp_file,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            sorted(known_servers),
            file,
            indent=2,
            ensure_ascii=False,
        )

    os.replace(
        temp_file,
        KNOWN_SERVERS_FILE,
    )


def get_next_server_index():
    os.makedirs(
        SERVERS_DIR,
        exist_ok=True,
    )

    max_index = 0

    for filename in os.listdir(SERVERS_DIR):
        if not filename.startswith(
            "NewGeneratedServer"
        ):
            continue

        if not filename.endswith(".json"):
            continue

        number = filename[
            len("NewGeneratedServer"):
            -len(".json")
        ]

        try:
            index = int(number)

            if index > max_index:
                max_index = index

        except ValueError:
            continue

    return max_index + 1


def process_uri(
    uri,
    known_servers,
    worker_id,
    known_lock,
):
    """
    Parse and test one URI.

    Only testing happens in parallel.
    Permanent server numbering and remarks
    are handled later in the main thread.
    """

    fingerprint = generate_fingerprint(uri)

    # Prevent duplicate processing.
    with known_lock:
        if fingerprint in known_servers:
            return None

        # Reserve fingerprint immediately so two
        # workers cannot test the same URI.
        known_servers.add(fingerprint)

    try:
        parsed = parse_uri(uri)

        if not parsed:
            return None

        local_port = (
            BASE_TEST_PORT + worker_id
        )

        temp_config = generate_xray_json(
            parsed,
            is_temp=True,
            local_port=local_port,
        )

        result = test_server(
            temp_config,
            local_port,
        )

        log_result(
            parsed.get(
                "protocol",
                "unknown",
            ),
            parsed.get(
                "host",
                "unknown",
            ),
            parsed.get(
                "port",
                0,
            ),
            result,
        )

        if result.get("status") != "WORKING":
            return None

        return {
            "fingerprint": fingerprint,
            "parsed": parsed,
            "result": result,
        }

    except Exception as exc:
        print(
            f"[ERROR] Failed to process URI: "
            f"{type(exc).__name__}: {exc}"
        )

        return None


def save_server(
    index,
    final_config,
):
    os.makedirs(
        SERVERS_DIR,
        exist_ok=True,
    )

    filename = (
        f"{SERVERS_DIR}/"
        f"NewGeneratedServer{index}.json"
    )

    temp_filename = (
        f"{filename}.tmp"
    )

    with open(
        temp_filename,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            final_config,
            file,
            indent=2,
            ensure_ascii=False,
        )

    os.replace(
        temp_filename,
        filename,
    )

    return filename


def main():
    print(
        "Starting VPN Key Scanner & Generator..."
    )

    os.makedirs(
        SERVERS_DIR,
        exist_ok=True,
    )

    known_servers = load_known_servers()

    print(
        f"Known servers: "
        f"{len(known_servers)}"
    )

    try:
        with open(
            "sources.txt",
            "r",
            encoding="utf-8",
        ) as file:
            sources = [
                line.strip()
                for line in file
                if line.strip()
                and not line.lstrip().startswith("#")
            ]

    except OSError as exc:
        print(
            f"[ERROR] Cannot read sources.txt: "
            f"{exc}"
        )
        return

    if not sources:
        print(
            "[ERROR] sources.txt is empty."
        )
        return

    print(
        f"Sources: {len(sources)}"
    )

    all_uris = fetch_and_extract_uris(
        sources
    )

    print(
        f"Extracted "
        f"{len(all_uris)} unique URI(s)."
    )

    if not all_uris:
        print(
            "No URI found."
        )

        save_known_servers(
            known_servers
        )

        return

    new_working_servers = []

    known_lock = threading.Lock()

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = []

        for index, uri in enumerate(
            all_uris
        ):
            worker_id = (
                index % MAX_WORKERS
            )

            future = executor.submit(
                process_uri,
                uri,
                known_servers,
                worker_id,
                known_lock,
            )

            futures.append(future)

        for future in concurrent.futures.as_completed(
            futures
        ):
            try:
                result = future.result()

                if result:
                    new_working_servers.append(
                        result
                    )

            except Exception as exc:
                print(
                    f"[ERROR] Worker failed: "
                    f"{type(exc).__name__}: {exc}"
                )

    # Save fingerprints even when no server worked.
    save_known_servers(
        known_servers
    )

    if not new_working_servers:
        print(
            "\nNo new working servers found."
        )
        return

    print(
        f"\nFound "
        f"{len(new_working_servers)} "
        f"new working server(s)."
    )

    # --------------------------------------------------
    # IMPORTANT:
    # From this point onward everything is sequential.
    #
    # This prevents duplicate country numbers such as:
    #
    # 🇳🇱 Нидерланды #1
    # 🇳🇱 Нидерланды #1
    #
    # --------------------------------------------------

    next_index = get_next_server_index()

    saved_count = 0

    for server in new_working_servers:
        parsed = server["parsed"]
        result = server["result"]

        try:
            remark = generate_remark(
                result.get("country"),
                result.get("countryCode"),
            )

            final_config = generate_xray_json(
                parsed,
                is_temp=False,
                local_port=1080,
                remark=remark,
            )

            filename = save_server(
                next_index,
                final_config,
            )

            print(
                f"[SAVED] {filename} "
                f"→ {remark}"
            )

            next_index += 1
            saved_count += 1

        except Exception as exc:
            print(
                f"[ERROR] Failed to save server: "
                f"{type(exc).__name__}: {exc}"
            )

    save_known_servers(
        known_servers
    )

    print(
        f"\nFinished. "
        f"Saved {saved_count} server(s)."
    )


if __name__ == "__main__":
    main()
