"""
`commands/customise.py`

Fusion 360 CommandDialog for editing presence templates.

Opens a native Fusion dialog with text inputs for each customisable 
presence field, a token reference at the bottom and Save / Revert to 
Default / Cancel actions.
"""

import adsk.core
import adsk.fusion

from lib.template import load, save, DEFAULTS, TOKEN_REFERENCE
from typing import TYPE_CHECKING

if TYPE_CHECKING: from commands.presence import PresenceManager

CMD_ID = "fusionkit_discord_customise_presence"


def register(ui: adsk.core.UserInterface, manager: "PresenceManager") -> list:
    """
    Register the custom command definition.
    Returns a list of handlers to spare from the harsh reality of
    permanent death.
    """
    # clean up defs
    existing = ui.commandDefinitions.itemById(CMD_ID)
    if existing:
        try:
            existing.deleteMe()
        except Exception:...

    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID,
        "Customise Presence",
        "Edit the Discord rich presence template strings.",
        "",
    )

    handlers: list = []
    handler = _CustomiseCreatedHandler(manager, handlers)
    cmd_def.commandCreated.add(handler)
    handlers.append(handler)

    return handlers

def unregister(ui: adsk.core.UserInterface) -> None:
    existing = ui.commandDefinitions.itemById(CMD_ID)
    if existing:
        try:
            existing.deleteMe()
        except Exception:...


# ---------------------------------------
#       HANDLERS
# ---------------------------------------

class _CustomiseCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, manager: "PresenceManager", handler_store: list):
        super().__init__()
        self._manager = manager
        self._handler_store = handler_store
        self._execute_handler: adsk.core.CommandEventHandler | None = None
        self._destroy_handler: adsk.core.CommandEventHandler | None = None

    def notify(self, args: adsk.core.CommandCreatedEventArgs) -> None:
        cmd = args.command
        cmd.isOKButtonVisible = True
        cmd.okButtonText = "Save"
        cmd.isCancelButtonVisible = True    # type: ignore

        inputs = cmd.commandInputs

        # load current templates
        templates = load()

        # text fields
        inputs.addStringValueInput(
            "details",
            "Details",
            templates["details"],
        )
        inputs.addStringValueInput(
            "state",
            "State",
            templates["state"],
        )
        inputs.addStringValueInput(
            "large_text",
            "Large Icon Tooltip",
            templates["large_text"],
        )
        inputs.addStringValueInput(
            "idle_text",
            "Idle Text",
            templates["idle_text"],
        )
        inputs.addStringValueInput(
            "privacy_text",
            "Privacy Mode Text",
            templates["privacy_text"],
        )

        # revert button
        inputs.addBoolValueInput(
            "revert",
            "Revert to Defaults",
            False,
            "",
            False,
        )

        inputs.addTextBoxCommandInput(
            "token_ref",
            "Available Tokens",
            _build_token_reference_html(),
            6,
            True
        )

        # wire handlers 
        self._execute_handler = _CustomiseExecuteHandler(self._manager)
        cmd.execute.add(self._execute_handler)
        self._handler_store.append(self._execute_handler)

        self._input_changed_handler = _InputChangedHandler(inputs)
        cmd.inputChanged.add(self._input_changed_handler)
        self._handler_store.append(self._input_changed_handler)

        self._destroy_handler = _CustomiseDestroyHandler(self._handler_store)
        cmd.destroy.add(self._destroy_handler)
        self._handler_store.append(self._destroy_handler)

class _InputChangedHandler(adsk.core.InputChangedEventHandler):
    """Handles the Revert to Defaults action."""
    def __init__(self, inputs: adsk.core.CommandInputs) -> None:
        super().__init__()
        self._inputs = inputs

    def notify(self, args: adsk.core.InputChangedEventArgs) -> None:
        if args.input.id == "revert":
            for key, value in DEFAULTS.items():
                inp = self._inputs.itemById(key)
                if inp: inp.value = value # type: ignore[attr-defined]

class _CustomiseExecuteHandler(adsk.core.CommandEventHandler):
    """Saves templates and pushes a fresh presence update"""
    def __init__(self, manager: "PresenceManager") -> None:
        super().__init__()
        self._manager = manager

    def notify(self, args: adsk.core.CommandEventArgs) -> None:
        inputs = args.command.commandInputs

        templates: dict[str, str] = {}
        for key in DEFAULTS:
            inp = inputs.itemById(key)
            if inp: templates[key] = inp.value      # type: ignore[attr-defined]

        save(templates)
        self._manager.reload_templates()

class _CustomiseDestroyHandler(adsk.core.CommandEventHandler):
    """Cleans up execute/inputCharged handlers on dialog close"""
    def __init__(self, handler_store: list) -> None:
        super().__init__()
        self._handler_store = handler_store

    def notify(self, args: adsk.core.CommandEventArgs) -> None:...

# -----------------------------------------------
#       HELPERS
# -----------------------------------------------

def _build_token_reference_html() -> str:
    rows = "".join(
        f"<tr><td><b>{token}</b></td><td>{desc}</td></tr>" 
        for token, desc in TOKEN_REFERENCE
    )
    return (
        "<style>td { padding: 2px 8px; }</style>"
        "<table>"
        f"{rows}"
        "</table>"
    )