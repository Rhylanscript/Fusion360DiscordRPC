# Fusion360DiscordRPC

A customisable Fusion 360 Add-in that shows your current activity in discord via Rich Presence.

Example previews:

![Discord Rich Presence Preview][preview]
![Fusion 360 View on Toolbar using FusionkitAPI][preview2]

## Features

- Shows the active document name
- Shows component count and active workspace
- Elapsed timer from when the add-in was loaded
- Updates automatically when document is switched
- Has a 'privacy mode' option which hides document name
- Full presence customisation through popup window
  ![Customisation Window][customise]

## Requirements

### Software Requirements

You must have the following software installed:

- Autodesk Fusion 360 (shocking)
- Discord (**desktop app**, _must_ be running for presence to show)

### Dependencies

No external pip dependencies are required for this addin however:

It is recommended to have a copy of the FusionkitRibbonAPI add-in, which can be found at [this repository][fusionkit]. Note that without this dependency, the add-in will have no ribbon functionality and be limited to solely showing rich presence, without customisation.

## Setup

### 1. Configure the Client ID (optional)

A default Client ID is already provided in `config/client.py`. If you want to use your own Discord application (custom app name or assets), replace it with your own application ID:

1. Go to the [Discord Developer Portal][portal] and click **New Application**
2. Copy the **Application ID** from the **General Information** page
3. Open `config/client.py` and replace the default `CLIENT_ID`
4. Go to **Rich Presence > Art Assets** and upload the [Fusion360 logo][logo] with the key `fusion360`

### 2. Install the Add in

Copy (or symlink) the entire root folder into Fusion360's addins directory, ensure the folder name remains as `Fusion360DiscordRPC`:

| OS      | Path                                                                     |
| ------- | ------------------------------------------------------------------------ |
| Windows | `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\`                     |
| macOS   | `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/` |

Additionally, a release of the [FusionkitRibbonAPI][fusionkit] dependency must be placed inside the same AddIns folder, ensuring the name remains as `FusionkitRibbonAPI`.

### 3. Run it

1. Open Fusion360 and press `Shift+S` to open scripts & addins
2. Go to the **Add-Ins** tab and find **Fusion360DiscordRPC**
3. Toggle it on (or run it) - the window will close
4. **IMPORTANT** Make sure you have discord open before you run it!

**Optionally:** Check the **Run on Startup** box to load it automatically every time Fusion opens.

## VSCode Setup

Install the recommended extensions when prompted. Pylance uses the `.vscode/settings.json` to resolve `adsk.*` imports from Fusion's python scripts.

If you get `reportMissingImports` errors on `adsk`, verify that Fusion's stub dir exists at the paths provided in `settings.json`. Running any builtin scripts from the Scripts & Addins panel will generate the stubs if they're missing.

If all else fails, replace the entries in settings.json with the direct paths (not recommended):

```json
{
  "python.analysis.extraPaths": [
    "{your path prefix here}/AppData/Roaming/Autodesk/Autodesk Fusion 360/API/Python/defs",
    "{path prefix}/AppData/Roaming/Autodesk/Autodesk Fusion 360/API/Addins/FusionkitRibbonAPI"
  ]
  // rest of the json data like normal
}
```

## What is Shown

| Field   | Value                                                 |
| ------- | ----------------------------------------------------- |
| Details | `Designing "{<document name>` or `in Fusion 360}"`    |
| State   | `<N> components · <workspace>`                        |
| Elapsed | Time since the addin was loaded                       |
| Icon    | Fusion 360 Logo in `assets/` (provided you do step 1) |

## Configuration

Edit the constants found in `config/config.py`:

```python
POLL_INTERVAL = 15              # Seconds between background refreshes
LARGE_IMAGE_KEY = "fusion360"   # Must match the key in the Discord Dev Portal
```

## Project Structure

```text
Fusion360DiscordRPC/                  # root directory
├── .vscode/                          # VSCode configuration files
│   ├── extensions.json               # Recommended VSCode extensions
│   ├── launch.json                   # Fusion debugger config
│   └── settings.json                 # pylance paths for adsk.* files
│
├── resources/                        # folder for project resources
│   ├── fusionkit_discord_.../        # resources for button icons
│   │   └── ...
│   ├── fusion360.png                 # Fusion 360 logo for Dev Portal
│   └── ... (other files)             # any README assets / log files
│
├── commands/                         # folder containing command logic
│   ├── customise.py                  # logic to customise presence 
│   ├── presence.py                   # houses all presence logic 
│   └── ribbon.py                     # FusionkitRibbonAPI call logic
│
├── config/                           # folder containing config files
│   ├── client.py                     # contains the CLIENT_ID
│   └── config.py                     # contains configuration values 
│
├── handlers/                         # folder event handlers
│   └── document.py                   # document event handlers in here 
│
├── lib/                              # folder containing command logic
│   ├── discord_ipc.py                # Discord IPC client  
│   └── template.py                   # manage tokens in customisation
│
├── Fusion360DiscordRPC.manifest      # addin metadata
├── Fusion360DiscordRPC.py            # addin entrypoint
│
└── README.md                         # Project README file
```

## How it works

Fusion 360 Addins are Python scripts that are loaded into Fusion at runtime. This addin hooks into Fusion's document events and runs on a background thread that polls every 15 seconds by default. On each update it reads the active document name and component count in the doc then sends a `SET_ACTIVITY` command through to Discord using a local IPC socket which is a named pipe on windows (`\\.\pipe\discord-ipc-0`) or a unix socket on macOS.

The addin uses tokens to customise presence to read specific values from Fusion such as workspace details, file states and Fusion properties. These tokens can be referenced during customisation by calling them in braces (e.g. '{app_version}' will give Fusion 360's installed version).

By using FusionkitRibbonAPI, the add-in can hook into the fusion toolbar and create buttons to allow for additional functionality.

<!-- ASSET REFERENCES -->

[preview]: /resources/preview.png
[preview2]: /resources/preview2.png
[customise]: /resources/customise.png
[logo]: /resources/fusion360.png

<!-- LINK REFERENCES -->

[portal]: https://discord.com/developers/applications
[fusionkit]: https://github.com/Rhylanscript/FusionkitRibbonAPI/releases
