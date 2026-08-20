import time
import os
import network

try:
    import ujson as json
except Exception:
    import json

try:
    import urequests as requests
except Exception:
    import requests

from lib import display
from lib.hydra.config import Config
from lib.userinput import UserInput
from font import vga1_8x16 as font


BASE_URL = "http://example.com/cardputer"
MANIFEST_URL = BASE_URL + "/manifest.txt"

WIFI_DB_PATHS = [
    "/wifi_profiles.json",
    "wifi_profiles.json",
]

LOCAL_APPS_DIRS = [
    "/sd/apps",
    "/apps",
    "apps",
]


cfg = Config()
tft = display.Display(use_tiny_buf=True)
kb = UserInput()
wlan = network.WLAN(network.STA_IF)


def draw(lines):
    tft.fill(cfg.palette[2])

    y = 4

    for line in lines[:8]:
        tft.text(
            str(line)[:29],
            4,
            y,
            cfg.palette[8],
            font=font
        )

        y += 16

    tft.show()


def get_new_keys():
    try:
        return [str(k) for k in kb.get_new_keys()]
    except Exception:
        return []


def keys_upper():
    return [k.upper() for k in get_new_keys()]


def exit_pressed(keys=None):
    if keys is None:
        keys = keys_upper()

    return "ESC" in keys or "Q" in keys


def wait_key_or_timeout(seconds=2):
    start = time.ticks_ms()

    while time.ticks_diff(
        time.ticks_ms(),
        start
    ) < seconds * 1000:

        keys = keys_upper()

        if keys:
            return keys

        time.sleep_ms(80)

    return []


def wait_choice(valid, title, lines=None):
    valid = [x.upper() for x in valid]

    while True:
        screen = [title]

        if lines:
            screen.extend(lines)

        draw(screen)

        for key in keys_upper():
            if key in valid:
                return key

            if key in ("ESC", "Q"):
                return None

        time.sleep_ms(80)


def input_text(title, secret=False, initial=""):
    value = initial

    while True:
        if secret:
            shown = "*" * len(value)
        else:
            shown = value

        draw([
            title,
            shown[-28:],
            "ENTER = OK",
            "ESC = anuluj",
            "BKSP = usun znak",
        ])

        raw_keys = get_new_keys()

        for key in raw_keys:
            upper = key.upper()

            if upper in ("ESC", "Q"):
                return None

            if upper in ("ENTER", "RETURN"):
                return value

            if upper in (
                "BSPC",
                "BACKSPACE",
                "BKSP",
                "DEL",
            ):
                value = value[:-1]
                continue

            if len(key) == 1 and len(value) < 63:
                value += key

        time.sleep_ms(60)


def get_local_apps_dir():
    for directory in LOCAL_APPS_DIRS:
        try:
            try:
                os.mkdir(directory)
            except Exception:
                pass

            test = directory + "/.sync_test"

            with open(test, "w") as f:
                f.write("ok")

            try:
                os.remove(test)
            except Exception:
                pass

            return directory

        except Exception:
            pass

    return "."


LOCAL_APPS_DIR = get_local_apps_dir()


# --------------------------------------------------
# Wi-Fi profiles
# --------------------------------------------------

def load_wifi_db():
    for path in WIFI_DB_PATHS:
        try:
            with open(path, "r") as f:
                data = json.loads(f.read())

            if not isinstance(data, dict):
                continue

            if (
                "profiles" not in data
                or not isinstance(data["profiles"], list)
            ):
                data["profiles"] = []

            if "default" not in data:
                data["default"] = ""

            return data, path

        except Exception:
            pass

    return {
        "default": "",
        "profiles": [],
    }, WIFI_DB_PATHS[-1]


def save_wifi_db(data, preferred_path=None):
    paths = []

    if preferred_path:
        paths.append(preferred_path)

    for path in WIFI_DB_PATHS:
        if path not in paths:
            paths.append(path)

    payload = json.dumps(data)

    for path in paths:
        try:
            with open(path, "w") as f:
                f.write(payload)

            return path

        except Exception:
            pass

    return None


def get_profile(ssid):
    db, _ = load_wifi_db()

    for profile in db["profiles"]:
        if profile.get("ssid") == ssid:
            return profile

    return None


def get_default_profile():
    db, _ = load_wifi_db()

    default_ssid = db.get("default", "")

    for profile in db["profiles"]:
        if profile.get("ssid") == default_ssid:
            return profile

    if db["profiles"]:
        return db["profiles"][0]

    return None


def store_profile(
    ssid,
    password,
    make_default=False
):
    db, path = load_wifi_db()

    found = False

    for profile in db["profiles"]:
        if profile.get("ssid") == ssid:
            profile["password"] = password
            found = True
            break

    if not found:
        db["profiles"].append({
            "ssid": ssid,
            "password": password,
        })

    if make_default or not db.get("default"):
        db["default"] = ssid

    return save_wifi_db(
        db,
        path
    ) is not None


def set_default_profile(ssid):
    db, path = load_wifi_db()

    exists = False

    for profile in db["profiles"]:
        if profile.get("ssid") == ssid:
            exists = True
            break

    if not exists:
        return False

    db["default"] = ssid

    return save_wifi_db(
        db,
        path
    ) is not None


def delete_profile(ssid):
    db, path = load_wifi_db()

    remaining = []

    for profile in db["profiles"]:
        if profile.get("ssid") != ssid:
            remaining.append(profile)

    db["profiles"] = remaining

    if db.get("default") == ssid:
        if remaining:
            db["default"] = remaining[0].get(
                "ssid",
                ""
            )
        else:
            db["default"] = ""

    return save_wifi_db(
        db,
        path
    ) is not None


# --------------------------------------------------
# Sync paths
# --------------------------------------------------

def safe_remote_path(name):
    name = name.strip().replace("\\", "/")

    while name.startswith("/"):
        name = name[1:]

    parts = []

    for part in name.split("/"):
        part = part.strip()

        if (
            not part
            or part == "."
            or part == ".."
        ):
            continue

        allowed = (
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789_-."
        )

        clean = "".join(
            c for c in part
            if c in allowed
        )

        if clean:
            parts.append(clean)

    if not parts:
        return None

    final = "/".join(parts)

    if not (
        final.endswith(".py")
        or final.endswith(".txt")
    ):
        return None

    return final


def ensure_parent_dirs(path):
    parts = path.split("/")[:-1]

    current = ""

    for part in parts:
        if part == "":
            current = "/"
            continue

        if current in ("", "/"):
            current = current + part
        else:
            current = current + "/" + part

        try:
            os.mkdir(current)
        except Exception:
            pass


def http_get_text(url):
    response = requests.get(url)

    try:
        text = response.text

    finally:
        try:
            response.close()
        except Exception:
            pass

    return text


# --------------------------------------------------
# Main menu
# --------------------------------------------------

def menu():
    connected = False
    ip = "-"

    try:
        connected = wlan.isconnected()

        if connected:
            ip = wlan.ifconfig()[0]

    except Exception:
        pass

    default_profile = get_default_profile()

    if default_profile:
        default_name = default_profile.get(
            "ssid",
            "-"
        )
    else:
        default_name = "-"

    draw([
        "Remote Sync Hub v2",
        "WiFi: " + (
            "ON " + ip
            if connected
            else "OFF"
        ),
        "1 Connect default",
        "3 Saved WiFi",
        "4 Sync Apps",
        "5 Scan / Connect",
        "Default: " + default_name[:20],
        "ESC/Q Exit",
    ])


# --------------------------------------------------
# Wi-Fi connection
# --------------------------------------------------

def connect_credentials(
    ssid,
    password
):
    wlan.active(True)

    try:
        if wlan.isconnected():
            wlan.disconnect()
            time.sleep_ms(250)

    except Exception:
        pass

    draw([
        "Lacze z Wi-Fi:",
        ssid[:26],
        "ESC/Q = anuluj",
    ])

    try:
        wlan.connect(
            ssid,
            password
        )

    except Exception as e:
        draw([
            "CONNECT ERROR",
            repr(e)[:28],
            "dowolny klawisz",
        ])

        wait_key_or_timeout(4)

        return False

    for i in range(25):
        keys = keys_upper()

        if exit_pressed(keys):
            try:
                wlan.disconnect()
            except Exception:
                pass

            return False

        if wlan.isconnected():
            ip = wlan.ifconfig()[0]

            draw([
                "POLACZONO!",
                ssid[:26],
                "IP:",
                ip,
                "dowolny klawisz",
            ])

            wait_key_or_timeout(3)

            return True

        draw([
            "Laczenie...",
            ssid[:26],
            str(i + 1) + "/25",
            "ESC/Q = anuluj",
        ])

        time.sleep(1)

    draw([
        "NIE POLACZONO",
        "Sprawdz haslo",
        "Siec musi byc 2.4GHz",
        "dowolny klawisz",
    ])

    wait_key_or_timeout(4)

    return False


def connect_wifi():
    profile = get_default_profile()

    if not profile:
        draw([
            "Brak zapisanej sieci",
            "Uruchamiam skan...",
        ])

        time.sleep_ms(700)

        scan_wifi()

        return False

    return connect_credentials(
        profile.get("ssid", ""),
        profile.get("password", "")
    )


# --------------------------------------------------
# Saved Wi-Fi menu
# --------------------------------------------------

def saved_wifi_menu():
    while True:
        db, _ = load_wifi_db()

        profiles = db["profiles"]

        if not profiles:
            draw([
                "Saved WiFi",
                "Brak zapisanych sieci",
                "5 w menu = skan",
                "ESC/Q = wroc",
            ])

            wait_key_or_timeout(4)

            return

        visible = profiles[:6]

        lines = [
            "Saved WiFi (* default)"
        ]

        for i, profile in enumerate(visible):
            if (
                profile.get("ssid")
                == db.get("default")
            ):
                mark = "*"
            else:
                mark = " "

            lines.append(
                str(i + 1)
                + mark
                + " "
                + profile.get(
                    "ssid",
                    ""
                )[:23]
            )

        lines.append(
            "1-6 wybierz, ESC wroc"
        )

        choice = wait_choice(
            [
                str(i + 1)
                for i in range(
                    len(visible)
                )
            ],
            lines[0],
            lines[1:]
        )

        if choice is None:
            return

        profile = visible[
            int(choice) - 1
        ]

        ssid = profile.get(
            "ssid",
            ""
        )

        action = wait_choice(
            ["C", "D", "X"],
            ssid[:28],
            [
                "C Connect",
                "D Set default",
                "X Delete",
                "ESC Back",
            ]
        )

        if action == "C":
            connect_credentials(
                ssid,
                profile.get(
                    "password",
                    ""
                )
            )

        elif action == "D":
            if set_default_profile(ssid):
                draw([
                    "Ustawiono domyslna:",
                    ssid[:28],
                ])
            else:
                draw([
                    "BLAD",
                    "Nie zapisano ustawien",
                ])

            wait_key_or_timeout(2)

        elif action == "X":
            confirm = wait_choice(
                ["Y", "N"],
                "Usunac profil?",
                [
                    ssid[:28],
                    "Y Yes / N No",
                ]
            )

            if confirm == "Y":
                delete_profile(ssid)


# --------------------------------------------------
# Synchronization
# --------------------------------------------------

def parse_manifest(text):
    files = []

    for line in text.splitlines():
        line = line.strip()

        if (
            not line
            or line.startswith("#")
        ):
            continue

        name = safe_remote_path(line)

        if name:
            files.append(name)

    output = []
    seen = set()

    for file_name in files:
        if file_name not in seen:
            output.append(file_name)
            seen.add(file_name)

    return output


def save_local(
    rel_path,
    content
):
    local_path = (
        LOCAL_APPS_DIR
        + "/"
        + rel_path
    )

    ensure_parent_dirs(
        local_path
    )

    with open(
        local_path,
        "w"
    ) as f:
        f.write(content)

    return local_path


def sync_apps():
    if not wlan.isconnected():
        draw([
            "Sync Apps",
            "Brak Wi-Fi",
            "Najpierw 1 Connect",
            "dowolny klawisz",
        ])

        wait_key_or_timeout(4)

        return

    draw([
        "Sync Apps",
        "Pobieram manifest",
        MANIFEST_URL[-28:],
        "czekaj...",
    ])

    try:
        manifest = http_get_text(
            MANIFEST_URL
        )

    except Exception as e:
        draw([
            "MANIFEST ERROR",
            repr(e)[:28],
            "dowolny klawisz",
        ])

        wait_key_or_timeout(6)

        return

    files = parse_manifest(
        manifest
    )

    if not files:
        draw([
            "Sync Apps",
            "manifest pusty",
            "Dodaj pliki .py",
            "dowolny klawisz",
        ])

        wait_key_or_timeout(6)

        return

    ok = 0
    fail = 0

    for idx, rel in enumerate(files):
        if exit_pressed():
            break

        draw([
            "Sync Apps",
            str(idx + 1)
            + "/"
            + str(len(files)),
            rel[:28],
            "pobieram...",
        ])

        url = (
            BASE_URL
            + "/"
            + rel
        )

        try:
            content = http_get_text(
                url
            )

            if len(content) < 1:
                fail += 1
                continue

            save_local(
                rel,
                content
            )

            ok += 1

        except Exception as e:
            fail += 1

            draw([
                "ERROR:",
                rel[:24],
                repr(e)[:28],
            ])

            time.sleep_ms(800)

    draw([
        "SYNC DONE",
        "OK: " + str(ok),
        "FAIL: " + str(fail),
        "Folder:",
        LOCAL_APPS_DIR[:26],
        "dowolny klawisz",
    ])

    wait_key_or_timeout(8)


# --------------------------------------------------
# Scan and connect
# --------------------------------------------------

def scan_wifi():
    try:
        wlan.active(True)

        draw([
            "Skanuje Wi-Fi...",
            "czekaj...",
        ])

        time.sleep_ms(600)

        networks = wlan.scan()

        networks = sorted(
            networks,
            key=lambda x: x[3],
            reverse=True
        )

        unique = []
        seen = set()

        for net in networks:
            if isinstance(
                net[0],
                bytes
            ):
                ssid = net[0].decode()
            else:
                ssid = str(net[0])

            if (
                not ssid
                or ssid in seen
            ):
                continue

            seen.add(ssid)

            rssi = net[3]

            if len(net) > 4:
                auth = net[4]
            else:
                auth = 1

            unique.append((
                ssid,
                rssi,
                auth
            ))

            if len(unique) >= 6:
                break

        if not unique:
            draw([
                "Scan WiFi",
                "Brak sieci",
                "dowolny klawisz",
            ])

            wait_key_or_timeout(3)

            return

        lines = [
            "Scan WiFi - wybierz"
        ]

        for i, net in enumerate(unique):
            ssid = net[0]
            rssi = net[1]

            lines.append(
                str(i + 1)
                + " "
                + ssid[:18]
                + " "
                + str(rssi)
            )

        lines.append(
            "1-6 lub ESC"
        )

        choice = wait_choice(
            [
                str(i + 1)
                for i in range(
                    len(unique)
                )
            ],
            lines[0],
            lines[1:]
        )

        if choice is None:
            return

        ssid, rssi, auth = unique[
            int(choice) - 1
        ]

        old_profile = get_profile(
            ssid
        )

        if old_profile:
            password = old_profile.get(
                "password",
                ""
            )
        else:
            password = ""

        # auth == 0 oznacza zwykle siec otwarta
        if auth != 0:
            entered = input_text(
                "Haslo: " + ssid[:20],
                True,
                password
            )

            if entered is None:
                return

            password = entered

        if not connect_credentials(
            ssid,
            password
        ):
            return

        save_choice = wait_choice(
            ["S", "N"],
            "Zapisac ta siec?",
            [
                ssid[:28],
                "S Save / N No",
            ]
        )

        if save_choice != "S":
            return

        db, _ = load_wifi_db()

        first_profile = (
            len(db["profiles"]) == 0
        )

        make_default = first_profile

        if not first_profile:
            default_choice = wait_choice(
                ["Y", "N"],
                "Ustawic jako default?",
                [
                    "Y Yes / N No"
                ]
            )

            make_default = (
                default_choice == "Y"
            )

        if store_profile(
            ssid,
            password,
            make_default
        ):
            draw([
                "Siec zapisana",
                ssid[:28],
                "Default: "
                + (
                    "YES"
                    if make_default
                    else "NO"
                ),
            ])

        else:
            draw([
                "BLAD ZAPISU PROFILU",
                ssid[:28],
            ])

        wait_key_or_timeout(3)

    except Exception as e:
        draw([
            "SCAN ERROR",
            repr(e)[:28],
            "dowolny klawisz",
        ])

        wait_key_or_timeout(5)


# --------------------------------------------------
# Main loop
# --------------------------------------------------

menu()

while True:
    keys = keys_upper()

    if exit_pressed(keys):
        break

    if "1" in keys:
        connect_wifi()
        menu()

    elif "3" in keys:
        saved_wifi_menu()
        menu()

    elif "4" in keys:
        sync_apps()
        menu()

    elif "5" in keys:
        scan_wifi()
        menu()

    time.sleep_ms(100)