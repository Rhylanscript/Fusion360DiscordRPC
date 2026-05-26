# Fusion360DiscordRPC

A Fusion 360 Add-in that shows your current activity in discord via Rich Presence.

Example preview:

![Discord Rich Presence Preview][preview]

## Features

- Shows the active document name
- Shows component count and active workspace
- Elapsed timer from when the add-in was loaded
- Updates automatically when document is switched

## Requirements

No external pip dependencies are required for this addin!

- Autodesk Fusion 360 (shocking)
- Discord (**desktop app**, _must_ be running)

## Setup

### 1. Create a Discord Application

1. Go to the [Discord Developer Portal][portal] and click **New Application**
2. Name it whatever you want (This is what the application will be shown as in the rich presence - "Fusion 360" or "Fusion360" is recommended)
3. Copy the **Application ID** from the **General Information** page
4. Go to **Rich Presence > Art Assets** and upload the [Fusion360 logo][logo], and set the key to `fusion360`

### 2. Configure the Add in

Create `config.py` in the root directory of this folder and in it paste your Application ID into `CLIENT_ID`:

```python
CLIENT_ID: str = "(paste application id here)"
```

### 3. Install the Add in

Copy (or symlink) the entire root folder into Fusion360's addins directory, ensure the folder name remains as `Fusion360DiscordRPC`:

| OS      | Path                                                                     |
| ------- | ------------------------------------------------------------------------ |
| Windows | `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\`                     |
| macOS   | `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/` |

### 4. Run it

1. Open Fusion360 and press `Shift+S` to open scripts & addins
2. Go to the **Add-Ins** tab and find **Fusion360DiscordRPC**
3. Toggle it on (or run it) - the window will close
4. **!!IMPORTANT!!** Make sure you have discord open before you run it!

Check the **Run on Startup** box to load it automatically every time Fusion opens.

## VSCode Setup

Install the recommended extensions when prompted. Pylance uses the `.vscode/settings.json` to resolve `adsk.*` imports from Fusion's python scripts.

If you get `reportMissingImports` errors on `adsk`, verify that Fusion's stub dir exists at the paths provided in `settings.json`. Running any builtin scripts from the Scripts & Addins panel will generate the stubs if they're missing.

If all else fails, replace the entries in settings.json with the direct path (not recommended):

```json
{
  "python.analysis.extraPaths": [
    "{your path prefix here}/AppData/Roaming/Autodesk/Autodesk Fusion 360/API/Python/defs"
  ]
  // rest of the code like normal
  // note that the second entry isn't required for this method
}
```

## What is Shown

| Field   | Value                                              |
| ------- | -------------------------------------------------- |
| Details | `Designing "<document name>"`                      |
| State   | `<N> components · <workspace>`                     |
| Elapsed | Time since the addin was loaded                    |
| Icon    | Fusion 360 Logo in `assets/` (provided you step 1) |

## Configuration

Edit the constants at the top of `Fusion360DiscordRPC.py`:

```python
POLL_INTERVAL = 15              # Seconds between background refreshes
LARGE_IMAGE_KEY = "fusion360"   # Must match the key in the Discord Dev Portal
```

## Project Structure

```text
Fusion360DiscordRPC/                # root directory
├── assets/                         # folder containing assets
│   ├── fusion360.png               # Fusion 360 logo for Dev Portal
│   └── ... (other files)           # any README assets / log files
│
├── .vscode/                        # VSCode configuration files
│   ├── extensions.json             # Recommended VSCode extensions
│   ├── launch.json                 # Fusion debugger config
│   └── settings.json               # pylance paths for adsk.* files
│
├── Fusion360DiscordRPC.manifest    # addin metadata
├── Fusion360DiscordRPC.py          # addin entrypoint
├── discord_ipc.py                  # Discord IPC client
├── config.py                       # contains your CLIENT_ID
│
└── README.md                       # Project README file
```

## How it works

Fusion 360 Addins are Python scripts that are loaded into Fusion at runtime. This addin hooks into Fusion's document events and runs on a background thread that polls every 15 seconds by default. On each update it reads the active document name and component count in the doc then sends a `SET_ACTIVITY` command through to Discord using a local IPC socket which is a named pipe on windows (`\\.\pipe\discord-ipc-0`) or a unix socket on macOS.

No external dependencies are required for this Add in.

<!-- ASSET REFERENCES -->

[preview]: /assets/preview.png
[logo]: /assets/logo.png

<!-- LINK REFERENCES -->

[portal]: https://discord.com/developers/applications
