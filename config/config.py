"""
`config/config.py`

All user facing config lives in this file.
"""

# DISCORD APP SETTINGS

LARGE_IMAGE_KEY: str = "fusion360"
"""
Asset key for the large presence icon on discord.

Must match an image uploaded under `Rich Presence > Art Assets`
in your Discord Developer Portal application.
"""

# BEHAVIOUR

POLL_INTERVAL: int = 15
"""
Seconds between background presence refreshes (ensures elapsed
timer keeps ticking).
"""