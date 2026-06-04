"""
`config/client.py`

Configuration file for client values, such as the Discord app client ID.
"""

# For the client ID, you can either create your own discord app at
# https://discord.com/developers/applications and copy the client ID
# here, or you can use the default client ID which is:
#   "1508443628799000576"

# Note that using the default client ID means that you cannot 
# customise the app name shown in your presence

# for more information on setup with a custom client ID, see:
#   README.md

CLIENT_ID: str = "1508443628799000576"

"""
The client ID assigned to the application.

Used to fetch presence information such as app name and icon from the 
app dashboard.
"""