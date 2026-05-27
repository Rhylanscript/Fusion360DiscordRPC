"""
`commands/ribbon.py`

Registers the Discord RPC panel and buttons via FusionkitRibbonAPI.

Call `setup()` in `run()`, `teardown()` in `stop()`. All
IDs are prefixed to avoid collisions with other add-ins.

If FusionkitRibbonAPI is not installed, setup() logs a warning and 
returns. The add-in continues to work, just without ribbon controls.
"""

import os

import adsk.core

from typing import TYPE_CHECKING
if TYPE_CHECKING: from commands.presence import PresenceManager

# Attempt to import Fusionkit
try:
    import FusionkitRibbonAPI as fusionkit
    HAS_FUSIONKIT = True
except ImportError:
    HAS_FUSIONKIT = False


# ICON PATHS
_HERE           = os.path.dirname(os.path.abspath(__file__))
_RESOURCES      = os.path.join(_HERE, "..", "resources")

TOGGLE_ICON     = os.path.join(_RESOURCES, "fusionkit_discord_toggle")
RECONNECT_ICON  = os.path.join(_RESOURCES, "fusionkit_discord_reconnect")

PANEL_ID = "discord_rpc"

# track enabled state and ui ref for status bar feedback
_enabled = True
_ui = None


def setup(manager: "PresenceManager", ui: adsk.core.UserInterface) -> None:
    """
    Register the Discord RPC panel in the Fusionkit tab.
    Safe to call every `run()`, idempotent via API.
    """

    global _ui
    _ui = ui

    if HAS_FUSIONKIT:
        panel: fusionkit.FusionkitPanel = fusionkit.register_panel(PANEL_ID, "Discord RPC")
        panel.add_button(
            id          = "toggle",
            name        = "Disable Presence",
            tooltip     = "Presence is active. Click to disable.",
            icon_path   = TOGGLE_ICON,
            on_execute  = lambda: _on_toggle(manager, panel),
            promoted    = True,
        )

        panel.add_button(
            id          = "reconnect",
            name        = "Reconnect",
            tooltip     = "Reconnect to Discord. Use if Discord wasn't open when Fusion started.",
            icon_path   = RECONNECT_ICON,
            on_execute  = lambda: _on_reconnect(manager, panel)
        )
    else:
        print(
            "[DiscordRPC] FusionkitRibbonAPI is not installed - "
            "ribbon controls unavailable. "
            "Install it from Install it from https://github.com/Rhylanscript/FusionkitRibbonAPI"
        )
        ui.messageBox(
            "FusionkitRibbonAPI is not installed.\n\n"
            "Discord RPC will still work, but ribbon controls\n"
            "(toggle and reconnect) won't be available.\n\n"
            "Install FusionkitRibbonAPI to enable them.",
            "Fusionkit - Missing Dependency",
        )
        return

def teardown() -> None:
    """Unregister the Discord RPC panel. Tab remains."""
    if HAS_FUSIONKIT: fusionkit.unregister_panel(PANEL_ID)


# BUTTON CALLBACKS

def _status(msg: str) -> None:
    """Write a non-blocking message to Fusion's status bar"""
    if _ui: _ui.statusMessage = msg

def _on_toggle(manager: "PresenceManager", panel) -> None:
    global _enabled
    _enabled = not _enabled

    if _enabled:
        manager.enable()
        panel.update_button("toggle",
            name    = "Disable Presence",
            tooltip = "Presence is active. Click to disable.",
        )
        _status("Discord RPC: presence enabled.")
    else:
        manager.disable()
        panel.update_button("toggle",
            name    = "Enable Presence",
            tooltip = "Presence is paused. Click to enable.",
        )
        _status("Discord RPC: presence paused.")

def _on_reconnect(manager: "PresenceManager", panel) -> None:
    global _enabled
    success = manager.reconnect()
 
    # sync toggle label
    _enabled = success
    
    if success:
        panel.update_button("toggle",
            name    = "Disable Presence",
            tooltip = "Presence is active. Click to disable.",
        )
        if _ui:
            _ui.messageBox(
                "Successfully reconnected to Discord.",
                "Discord RPC",
            )
    else:
        panel.update_button("toggle",
            name    = "Enable Presence",
            tooltip = "Presence is paused. Click to enable.",
        )
        if _ui:
            _ui.messageBox(
                "Could not connect to Discord.\n"
                "Make sure Discord is running and try again.",
                "Discord RPC",
            )