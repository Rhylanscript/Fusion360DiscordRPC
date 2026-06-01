"""
`lib/template.py`

Handles presence template storage and token substitution.


Templates are stored in `presence_template.json` next to the add-in
so they persist across updates and repo changes.
 
Available tokens:
    {document_name}    — active document name
    {workspace}        — active workspace name
    {component_count}  — e.g. "12 components"
    {app_version}      — Fusion 360 version string
"""

import json
import os

# ---------------------------------------
#       DEFAULTS
# ---------------------------------------

# default values for keys
DEFAULTS: dict[str, str] = {
    "details":      'Designing "{document_name}"',
    "state":        "{component_count} · {workspace}",
    "large_text":   "Autodesk Fusion 360",
    "idle_text":    "Idle",
    "privacy_text": "Working in Fusion 360"
}

# token references
TOKEN_REFERENCE: list[tuple[str, str]] = [
    ("{document_name}",     "The name of the active document"),
    ("{workspace}",         "The active workspace (e.g. Design, Manufacture)"),
    ("{component_count}",   "Number of components (e.g. '12 components')"),
    ("{app_version}",       "Fusion 360 version string"),
]

# ---------------------------------------
#       STORAGE PATH
# ---------------------------------------

def _template_path() -> str:
    """Return the absolute path to `presence_template.json`."""
    addin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(addin_dir, "presence_template.json")

# ---------------------------------------
#       LOAD / SAVE
# ---------------------------------------

def load() -> dict[str, str]:
    """
    Load templates from disk, falling back to defaults for missing 
    keys.

    Returns:
        dict[str, str]: Dictionary of template strings keyed by field name.
    """
    path = _template_path()
    templates = dict(DEFAULTS)

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)

            # only accept known keys use DEFAULTS as fallback
            for key in DEFAULTS:
                if key in saved and isinstance(saved[key], str):
                    templates[key] = saved[key]

        except Exception as e:
            print(f"[template] Failed to load presence_template.json : {str(e)}")

    return templates

def save(templates: dict[str, str]) -> None:
    """
    Save templates to disk.

    Args:
        templates (dict[str, str]): Dict of template strings keyed by field name.
    """
    path = _template_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(templates, f, indent=2)
    except Exception as e:
        print(f"[template] Failed to save presence_template.json : {str(e)}")

# ---------------------------------------
#       TOKEN SUBSTITUTION
# ---------------------------------------

def render(template: str, tokens: dict[str, str]) -> str:
    """
    Substitute tokens in template string.
 
    Unknown tokens are left normally rather than raising an error.
 
    Args:
        template (str): Template string containing {token} placeholders.
        tokens (dict[str, str]): Dict of token name -> value.
 
    Returns:
        str: Rendered string with tokens replaced
    """
    result = template
    for key, value in tokens.items():
        result = result.replace(f"{{{key}}}", value)
    return result

def build_tokens(
    document_name: str,
    workspace: str,
    component_count: str,
    app_version: str,
) -> dict[str, str]:
    """
    Build the token dictionary from Fusion state values.
 
    Args:
        document_name (str):    Active document name
        workspace (str):        Active workspace name
        component_count (str):  Formatted component count string
        app_version (str):      fusion version string
 
    Returns:
        Dict suitable for passing to `render()`.
    """
    return {
        "document_name":    document_name,
        "workspace":        workspace,
        "component_count":  component_count,
        "app_version":      app_version,
    }