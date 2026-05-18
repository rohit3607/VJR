import asyncio
import os, sys
from os import environ

API_ID = int(environ.get("API_ID", "20959976"))
API_HASH = environ.get("API_HASH", "4f648d2c4c0fd1b89a995bb85b2dba67")
BOT_TOKEN = environ.get("BOT_TOKEN", "7520786912:AAHVWUMSGYh1_45k6dJemeL1C_sSZlmAIqg")

PORT = int(os.environ.get("PORT", 8080))
# Make Bot Admin In Log Channel With Full Rights
LOG_CHANNEL = int(environ.get("LOG_CHANNEL", "-1001868871195"))

ADMINS = [
    int(x)
    for x in environ.get(
        "ADMINS",
        "7955996369 7742380400 8454765899"
    ).split()
]

# Warning - Give Db uri in deploy server environment variable, don't give in repo.
DB_URI = environ.get("DB_URI", "mongodb+srv://rohitplayer87089:rohit870@cluster0.4wt927p.mongodb.net/?retryWrites=true&w=majority") # Warning - Give Db uri in deploy server environment variable, don't give in repo.
DB_NAME = environ.get("DB_NAME", "Req")

# If this is True Then Bot Accept New Join Request 
NEW_REQ_MODE = bool(environ.get('NEW_REQ_MODE', True))
