"""
`commands/customise.py`

Opens an HTML palette for editing Discord Presence templates.

The palette is a fixed-size webview window centered on screen,
Communication with the HTML/JS frontend uses Fusions palette
message system:

 > Python -> HTML : palette.sendInfoToHTML("load", json)
 > HTML -> Python : incomingFromHTML event -> handler

Actions sent from HTML:
```
    { "action": "save", "templates": { ... } }
    { "action": "cancel }
```
"""

import os
import json

import adsk.core
import adsk.fusion

from lib.template import load, save
from typing import TYPE_CHECKING

if TYPE_CHECKING: from commands.presence import PresenceManager

CMD_ID = "fusionkit_discord_customise_presence"

# ---------------------------------------
#       CONSTANTS
# ---------------------------------------

PALETTE_ID      = "fusionkit_discord_customise_palette"

_HERE           = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HTML_PATH      = os.path.join(_HERE, "resources", "customise", "index.html")

PALETTE_WIDTH   = 480
PALETTE_HEIGHT  = 560

def _html_url() -> str:
    """Convert local file path to a URL Fusions palette can load."""
    return "file:///" + _HTML_PATH.replace("\\", "/")

# ---------------------------------------
#       PUBLIC API
# ---------------------------------------

def open_palette(ui: adsk.core.UserInterface, manager: "PresenceManager") -> list:
    """
    Open or focus the customise palette.
    Returns a list of handlers to spare from death.
    """
    handlers: list = []

    # reuse existing palette if already open
    palette = ui.palettes.itemById(PALETTE_ID)
    if palette:
        palette.isVisible = True
        _send_templates(palette)
        return handlers
    
    palette = ui.palettes.add(
        PALETTE_ID,
        "Customise Discord Rich Presence",
        _html_url(),
        True,           # isVisible
        True,           # showCloseButton
        True,           # isResizable
        PALETTE_WIDTH,
        PALETTE_HEIGHT,
    )

    # center on screen
    palette.left = (1920 - PALETTE_WIDTH) // 2
    palette.top = (1080 - PALETTE_HEIGHT) // 2

    # wire incoming message handler
    handler = _IncomingHandler(ui, manager)
    palette.incomingFromHTML.add(handler)
    handlers.append(handler)

    # wire closed handler
    closed_handler = _ClosedHandler(handlers)
    palette.closed.add(closed_handler)
    handlers.append(closed_handler)

    return handlers


def close_palette(ui: adsk.core.UserInterface) -> None:
    """Close and delete the palette if it exists"""
    palette = ui.palettes.itemById(PALETTE_ID)
    if palette:
        try:
            palette.deleteMe()
        except Exception:...


# ---------------------------------------
#       HELPERS
# ---------------------------------------

def _send_templates(palette: adsk.core.Palette) -> None:
    """Send current templates to HTML frontend"""
    templates = load()
    palette.sendInfoToHTML("load", json.dumps({ "templates": templates }))

# ---------------------------------------
#       HANDLERS
# ---------------------------------------

class _IncomingHandler(adsk.core.HTMLEventHandler):
    def __init__(
        self,
        ui: adsk.core.UserInterface,
        manager: "PresenceManager",
    ) -> None:
        super().__init__()
        self._ui = ui
        self._manager = manager

    def notify(self, args: adsk.core.HTMLEventArgs) -> None:
        try:
            data: dict = json.loads(args.data)
            action = data.get("action")

            if action == "save":
                templates = data.get("templates", {})
                save(templates)
                self._manager.reload_templates()

            elif action == "cancel":
                close_palette(self._ui)

            elif action == "ready":
                # html signals if its ready to recv data
                palette = self._ui.palettes.itemById(PALETTE_ID)
                if palette: _send_templates(palette)

        except Exception as e:
            print(f"[customise] incoming message error: {e}")


class _ClosedHandler(adsk.core.UserInterfaceGeneralEventHandler):
    def __init__(self, handler_store: list):
        super().__init__()
        self._handler_store = handler_store

    def notify(self, args: adsk.core.UserInterfaceGeneralEventArgs) -> None:
        self._handler_store.clear()