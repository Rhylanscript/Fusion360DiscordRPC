"""
`commands/ribbon.py`

Owns the FusionKit ribbon tab, the Discord RPC panel and 
all controls.

Structure:
    Workspace: DesignWorkspace
      > Tab:   FusionKit        (FUSIONKIT_TAB_ID)
          > Panel: Discord RPC  (FUSIONKIT_DISCORD_PANEL_ID)
              > Toggle: Enable presence
              > Button: Reconnect

Call `setup()` in `run()`, `teardown()` in `stop()`. All
IDs are prefixed to avoid collisions with other add-ins.
"""

import os
import adsk.core    # type: ignore
import adsk.fusion  # type: ignore

from commands.presence import PresenceManager

# STABLE IDS

FUSIONKIT_TAB_ID            = "fusionkit_tab"
FUSIONKIT_DISCORD_PANEL_ID  = "fusionkit_discord_rpc_panel"

TOGGLE_CMD_ID               = "fusionkit_discord_toggle_presence"
RECONNECT_CMD_ID            = "fusionkit_discord_reconnect"

DESIGN_WORKSPACE            = "FusionSolidEnvironment"

# ICON PATHS
_HERE           = os.path.dirname(os.path.abspath(__file__))
_RESOURCES      = os.path.join(_HERE, "..", "resources")

TOGGLE_ICON     = os.path.join(_RESOURCES, "fusionkit_discord_toggle")
RECONNECT_ICON  = os.path.join(_RESOURCES, "fusionkit_discord_reconnect")


class RibbonManager:
    """
    Creates and tears down the FusionKit tab and Discord 
    RPC panel.

    Keeps references to every created object so `teardown()`
    can remove them cleanly in reverse order.
    """
    def __init__(
        self,
        ui: adsk.core.UserInterface,
        manager: PresenceManager,
    ) -> None:
        self._ui = ui
        self._manager = manager
        self._enabled = True

        # track created objs for teardown
        self._tab: adsk.core.ToolbarTab | None = None
        self._panel: adsk.core.ToolbarPanel | None = None

        self._toggle_def: adsk.core.CommandDefinition | None = None
        self._reconnect_def: adsk.core.CommandDefinition | None = None
        
        self._handlers: list = []


    # PUBLIC API

    def setup(self) -> None:
        """Create tab, panel and controls. safe to call on every `run()`."""

        workspace = self._ui.workspaces.itemById(DESIGN_WORKSPACE)
        if not workspace:
            print("[RibbonManager] Could not find DesignWorkspace - ribbon not created")
            return
        
        self._tab = self._get_or_create_tab(workspace)
        self._panel = self._get_or_create_panel()
        self._create_toggle()
        self._create_reconnect_button()

    def teardown(self) -> None:
        """Remove all controls, panel and tab created by add-in"""
        self._handlers.clear()

        for cmd_id in (TOGGLE_CMD_ID, RECONNECT_CMD_ID):
            self._delete_command_definition(cmd_id)

        if self._panel:
            try:
                self._panel.deleteMe()
            except Exception:...
            self._panel = None

        if self._tab:
            try:
                self._tab.deleteMe()
            except Exception:...
            self._tab = None

    # TAB / PANEL

    def _get_or_create_tab(self, workspace: adsk.core.Workspace) -> adsk.core.ToolbarTab:
        tab = workspace.toolbarTabs.itemById(FUSIONKIT_TAB_ID)
        if not tab:
            tab = workspace.toolbarTabs.add(FUSIONKIT_TAB_ID, "FusionKit")
        return tab
    
    def _get_or_create_panel(self) -> adsk.core.ToolbarPanel:
        if not self._tab:
            raise RuntimeError("Tab must exist before panel.")
        panel = self._tab.toolbarPanels.itemById(FUSIONKIT_DISCORD_PANEL_ID)
        if not panel:
            panel = self._tab.toolbarPanels.add(
                FUSIONKIT_DISCORD_PANEL_ID, "Discord RPC"
            )
        return panel
    
    # CONTROLS

    def _create_toggle(self) -> None:
        """Add a checkbox for enabling/disabling rich presence."""
        if not self._panel: return

        # clean up stale definitions
        self._delete_command_definition(TOGGLE_CMD_ID)

        toggle_def = self._ui.commandDefinitions.addButtonDefinition(
            TOGGLE_CMD_ID,
            "Disable Presence",
            "Presence is active. Click to disable.",
            TOGGLE_ICON
        )
        self._toggle_def = toggle_def

        handler = _ToggleCreatedHandler(self._manager, self)
        toggle_def.commandCreated.add(handler)
        self._handlers.append(handler)

        control = self._panel.controls.addCommand(toggle_def)
        control.isPromotedByDefault = True

    def _create_reconnect_button(self) -> None:
        """Add a button to reconnect to Discord IPC."""
        if not self._panel: return

        self._delete_command_definition(RECONNECT_CMD_ID)

        reconnect_def = self._ui.commandDefinitions.addButtonDefinition(
            RECONNECT_CMD_ID,
            "Reconnect",
            "Reconnect to Discord. Use if Discord wasn't open when Fusion launched.",
            RECONNECT_ICON,     # default icon path
        )
        self._reconnect_def = reconnect_def

        handler = _ReconnectCreatedHandler(self._manager, self)
        reconnect_def.commandCreated.add(handler)
        self._handlers.append(handler)

        self._panel.controls.addCommand(reconnect_def)

    # TOGGLE STATE HELPERS

    def set_enabled(self, enabled: bool) -> None:
        """Update local state and flip the button label"""
        self._enabled = enabled
        if self._toggle_def:
            self._toggle_def.name = "Disable Presence" if enabled else "Enable Presence"
            self._toggle_def.tooltip = "Presence is active. Click to disable." if enabled else "Presence is paused. Click to enable." 

        # non blocking status message
        msg = "Discord RPC: presence enabled." if enabled else "Discord RPC: presence paused."
        self._ui.statusMessage = msg 

    def sync_toggle_to_connected(self, connected: bool) -> None:
        """After a reconnect sync toggle label."""
        self.set_enabled(connected)

        if connected:
            self._ui.messageBox(
                "Successfully reconnected to Discord.",
                "Discord RPC",
                adsk.core.MessageBoxButtonTypes.OKButtonType,       # type: ignore
                adsk.core.MessageBoxIconTypes.InformationIconType,  # type: ignore
            )
        else:
            self._ui.messageBox(
                "Could not connect to Discord.\nEnsure Discord is running and try again.",
                "Discord RPC",
                adsk.core.MessageBoxButtonTypes.OKButtonType,       # type: ignore
                adsk.core.MessageBoxIconTypes.CriticalIconType,     # type: ignore
            )

    # HELPERS

    def _delete_command_definition(self, cmd_id: str) -> None:
        """Delete a CommandDefinition by ID if it exists."""
        existing = self._ui.commandDefinitions.itemById(cmd_id)
        if existing:
            try:
                existing.deleteMe()
            except Exception:...


# COMMAND HELPERS

class _ToggleCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, manager: PresenceManager, ribbon: RibbonManager) -> None:
        super().__init__()
        self._manager = manager
        self._ribbon = ribbon
        self._execute_handler: adsk.core.CommandEventHandler | None = None

    def notify(self, args: adsk.core.CommandCreatedEventArgs) -> None:
        self._execute_handler = _ToggleExecuteHandler(self._manager, self._ribbon)
        args.command.execute.add(self._execute_handler)

class _ToggleExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self, manager: PresenceManager, ribbon: RibbonManager) -> None:
        super().__init__()
        self._manager = manager
        self._ribbon = ribbon

    def notify(self, args: adsk.core.CommandEventArgs) -> None:
        try:
            if self._ribbon._enabled:
                self._manager.disable()
                self._ribbon.set_enabled(False)
            else:
                self._manager.enable()
                self._ribbon.set_enabled(True)

        except Exception as e:
            print(f"[ToggleHandler] error: {str(e)}")

class _ReconnectCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(
        self,
        manager: PresenceManager,
        ribbon: RibbonManager
    ) -> None:
        super().__init__()
        self._manager = manager
        self._ribbon = ribbon
        self._execute_handler: adsk.core.CommandEventHandler | None = None

    def notify(self, args: adsk.core.CommandCreatedEventArgs) -> None:
        self._execute_handler = _ReconnectExecuteHandler(self._manager, self._ribbon)
        args.command.execute.add(self._execute_handler)

class _ReconnectExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(
        self,
        manager: PresenceManager,
        ribbon: RibbonManager,
    ) -> None:
        super().__init__()
        self._manager = manager
        self._ribbon = ribbon

    def notify(self, args: adsk.core.CommandEventArgs) -> None:
        try:
            success = self._manager.reconnect()
            self._ribbon.sync_toggle_to_connected(success)
        except Exception as e:
            print(f"[ReconnectHandler] error: {str(e)}")