# Cardputer Remote Sync Hub

A MicroPython application for Cardputer that enables wireless app synchronization from a remote server to your device's SD card.

## Features

- **WiFi Connection** - Connect to local wireless networks
- **Remote App Sync** - Download and install apps from a web server
- **SD Card Integration** - Save apps directly to `/sd/apps`
- **Menu Integration** - Synced apps appear in the main menu

## Prerequisites

1. Cardputer device with [MicroHydra](https://github.com/nicokempe/MicroHydra) firmware installed
2. SD card formatted for the device
3. WiFi network (2.4GHz)

## Setup

### 1. Configure the App

Edit `remote_sync_hub.py` and update these variables:

```python
WIFI_SSID = "YourNetworkName"      # Your WiFi network name
WIFI_PASS = "YourPassword"         # Your WiFi password
BASE_URL = "http://example.com/cardputer"  # Your server URL
```

### 2. Prepare the Server

Place your app files on your web server and create a `manifest.txt` file listing all files to sync:

```
apps/my_app.py
apps/another_app.py
config/settings.txt
```

### 3. Install to Cardputer

1. Copy the configured `remote_sync_hub.py` file
2. Create a folder named `app` on your SD card
3. Place the file inside: `SD:/app/remote_sync_hub.py`
4. Insert the SD card into your Cardputer

## Usage

### First Time Setup

1. Power on your Cardputer with the SD card inserted
2. Navigate to and launch `remote_sync_hub` from the app menu
3. Press **1** to connect to WiFi
4. Wait for the connection confirmation with your IP address

### Syncing Apps

1. With WiFi connected, press **4** to sync apps
2. The app will download the manifest and all listed files
3. Files are saved to `/sd/apps` on your SD card
4. Synced apps will appear in the Cardputer main menu

### Menu Overview

| Key       | Action                       |
| --------- | ---------------------------- |
| **1**     | Connect to WiFi              |
| **4**     | Sync Apps from server        |
| **5**     | Scan available WiFi networks |
| **ESC/Q** | Exit the app                 |

## How It Works

1. **Connect** - The app connects to your WiFi network
2. **Fetch Manifest** - It downloads `manifest.txt` from your server
3. **Download Files** - Each file listed in the manifest is downloaded
4. **Save to SD** - Files are saved to `/sd/apps/` on the SD card
5. **Auto-Discover** - Cardputer's main menu automatically detects new apps

## Example Server Setup

Your web server should have this structure:

```
/cardputer/
├── manifest.txt
└── apps/
    ├── my_app.py
    └── game.py
```

Example `manifest.txt`:

```
apps/my_app.py
apps/game.py
```

## Troubleshooting

- **Connection Failed**: Verify WiFi credentials, ensure network is 2.4GHz (not 5GHz)
- **Sync Failed**: Check that your server is accessible and manifest.txt is valid
- **Apps Not Showing**: Ensure files are saved to `/sd/apps/` directory

## License

MIT License
