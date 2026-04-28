import time
import os
import network

try:
    import urequests as requests
except Exception:
    import requests

from lib import display
from lib.hydra.config import Config
from lib.userinput import UserInput
from font import vga1_8x16 as font

WIFI_SSID = ""
WIFI_PASS = ""

BASE_URL = "http://example.com/cardputer"
MANIFEST_URL = BASE_URL + "/manifest.txt"

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
        tft.text(str(line)[:29], 4, y, cfg.palette[8], font=font)
        y += 16
    tft.show()


def keys_upper():
    try:
        return [str(k).upper() for k in kb.get_new_keys()]
    except Exception:
        return []


def exit_pressed(keys=None):
    if keys is None:
        keys = keys_upper()
    return "ESC" in keys or "Q" in keys


def wait_key_or_timeout(seconds=2):
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < seconds * 1000:
        keys = keys_upper()
        if keys:
            return keys
        time.sleep_ms(80)
    return []


def get_local_apps_dir():
    for d in LOCAL_APPS_DIRS:
        try:
            try:
                os.mkdir(d)
            except Exception:
                pass

            test = d + "/.sync_test"
            with open(test, "w") as f:
                f.write("ok")
            try:
                os.remove(test)
            except Exception:
                pass
            return d
        except Exception:
            pass

    return "."


LOCAL_APPS_DIR = get_local_apps_dir()


def safe_remote_path(name):
    name = name.strip().replace("\\", "/")
    while name.startswith("/"):
        name = name[1:]

    # blokada przed ../
    parts = []
    for part in name.split("/"):
        part = part.strip()
        if not part or part == "." or part == "..":
            continue

        allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-."
        clean = "".join(c for c in part if c in allowed)
        if clean:
            parts.append(clean)

    if not parts:
        return None

    # na razie synchronizujemy tylko .py i .txt, żeby nie pobierać śmieci
    final = "/".join(parts)
    if not (final.endswith(".py") or final.endswith(".txt")):
        return None

    return final


def ensure_parent_dirs(path):
    # MicroPython nie ma zawsze makedirs, robimy ręcznie.
    parts = path.split("/")[:-1]
    cur = ""
    for part in parts:
        if part == "":
            cur = "/"
            continue

        if cur == "/" or cur == "":
            cur = cur + part
        else:
            cur = cur + "/" + part

        try:
            os.mkdir(cur)
        except Exception:
            pass


def http_get_text(url):
    r = requests.get(url)
    try:
        text = r.text
    finally:
        try:
            r.close()
        except Exception:
            pass
    return text


def menu():
    connected = False
    ip = "-"
    try:
        connected = wlan.isconnected()
        if connected:
            ip = wlan.ifconfig()[0]
    except Exception:
        pass

    draw([
        "Remote Sync Hub v1",
        "WiFi: " + ("ON " + ip if connected else "OFF"),
        "1 Connect WiFi",
        "4 Sync Apps",
        "5 Scan WiFi",
        "Folder:",
        LOCAL_APPS_DIR[:26],
        "ESC/Q Exit"
    ])


def connect_wifi():
    wlan.active(True)

    if wlan.isconnected():
        draw(["Wi-Fi juz polaczone", "IP:", wlan.ifconfig()[0], "dowolny klawisz"])
        wait_key_or_timeout(3)
        return True

    draw(["Lacze z Wi-Fi:", WIFI_SSID[:26], "ESC/Q = anuluj"])

    try:
        wlan.connect(WIFI_SSID, WIFI_PASS)
    except Exception as e:
        draw(["CONNECT ERROR", repr(e)[:28], "dowolny klawisz"])
        wait_key_or_timeout(4)
        return False

    for i in range(25):
        keys = keys_upper()
        if exit_pressed(keys):
            draw(["Anulowano", "dowolny klawisz"])
            wait_key_or_timeout(2)
            return False

        if wlan.isconnected():
            ip = wlan.ifconfig()[0]
            draw(["POLACZONO!", WIFI_SSID[:26], "IP:", ip, "dowolny klawisz"])
            wait_key_or_timeout(4)
            return True

        draw(["Laczenie...", WIFI_SSID[:26], str(i + 1) + "/25", "ESC/Q = anuluj"])
        time.sleep(1)

    draw(["NIE POLACZONO", "Sprawdz haslo/SSID", "Tylko 2.4GHz", "dowolny klawisz"])
    wait_key_or_timeout(5)
    return False


def parse_manifest(text):
    files = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = safe_remote_path(line)
        if name:
            files.append(name)

    # usuwamy duplikaty, zachowując kolejność
    out = []
    seen = set()
    for f in files:
        if f not in seen:
            out.append(f)
            seen.add(f)
    return out


def save_local(rel_path, content):
    local_path = LOCAL_APPS_DIR + "/" + rel_path
    ensure_parent_dirs(local_path)
    with open(local_path, "w") as f:
        f.write(content)
    return local_path


def sync_apps():
    if not wlan.isconnected():
        draw(["Sync Apps", "Brak Wi-Fi", "Najpierw 1 Connect", "dowolny klawisz"])
        wait_key_or_timeout(4)
        return

    draw(["Sync Apps", "Pobieram manifest", MANIFEST_URL[-28:], "czekaj..."])

    try:
        manifest = http_get_text(MANIFEST_URL)
    except Exception as e:
        draw(["MANIFEST ERROR", repr(e)[:28], "dowolny klawisz"])
        wait_key_or_timeout(6)
        return

    files = parse_manifest(manifest)

    if not files:
        draw(["Sync Apps", "manifest pusty", "Dodaj pliki .py", "dowolny klawisz"])
        wait_key_or_timeout(6)
        return

    ok = 0
    fail = 0

    for idx, rel in enumerate(files):
        if exit_pressed():
            break

        draw([
            "Sync Apps",
            str(idx + 1) + "/" + str(len(files)),
            rel[:28],
            "pobieram..."
        ])

        url = BASE_URL + "/" + rel

        try:
            content = http_get_text(url)
            if len(content) < 1:
                fail += 1
                continue

            save_local(rel, content)
            ok += 1

        except Exception as e:
            fail += 1
            draw(["ERROR:", rel[:24], repr(e)[:28]])
            time.sleep_ms(800)

    draw([
        "SYNC DONE",
        "OK: " + str(ok),
        "FAIL: " + str(fail),
        "Folder:",
        LOCAL_APPS_DIR[:26],
        "dowolny klawisz"
    ])
    wait_key_or_timeout(8)


def scan_wifi():
    try:
        wlan.active(True)
        draw(["Skanuje Wi-Fi...", "czekaj..."])
        time.sleep_ms(1000)
        nets = wlan.scan()
        nets = sorted(nets, key=lambda x: x[3], reverse=True)

        lines = ["Sieci Wi-Fi:"]
        if not nets:
            lines.append("brak")
        for n in nets[:7]:
            ssid = n[0].decode() if isinstance(n[0], bytes) else str(n[0])
            rssi = n[3]
            lines.append(ssid[:18] + " " + str(rssi))
        draw(lines)
    except Exception as e:
        draw(["SCAN ERROR", repr(e)[:28], "dowolny klawisz"])

    wait_key_or_timeout(8)


menu()

while True:
    keys = keys_upper()

    if exit_pressed(keys):
        break

    if "1" in keys:
        connect_wifi()
        menu()

    elif "4" in keys:
        sync_apps()
        menu()

    elif "5" in keys:
        scan_wifi()
        menu()

    time.sleep_ms(100)
