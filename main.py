@@ -1,51 +1,52 @@
import os
import time
from datetime import datetime, timezone
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID", "1410458084874260592")
AUTH_SECRET = os.getenv("AUTH_SECRET")  # Optional security
BOT_DISPLAY_NAME = os.getenv("BOT_DISPLAY_NAME", "CommandLoggerBot")

DISCORD_API_BASE = "https://discord.com/api/v10"

if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN environment variable is required!")

def auth_ok(req):
    """Validate optional auth header."""
    if not AUTH_SECRET:
        return True
    auth = req.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip()
        return token == AUTH_SECRET
    return False
    return auth == f"Bearer {AUTH_SECRET}"

def make_embed(payload):
    command = payload.get("command", "<unknown>")
    username = payload.get("username") or payload.get("user", "Unknown user")
    user_id = payload.get("user_id", payload.get("userId", "unknown"))
    username = payload.get("username", "Unknown user")
    user_id = payload.get("user_id", "unknown")
    description = payload.get("description", "No description provided.")
    bot_name = payload.get("bot_name", payload.get("bot", "Unknown Bot"))
    bot_name = payload.get("bot_name", "Unknown Bot")
    extra = payload.get("extra", {})

    # Build fields
    fields = [
        {"name": "Command / Trigger", "value": f"`{command}`", "inline": True},
        {"name": "Who triggered it", "value": f"{username} (`{user_id}`)", "inline": True},
        {"name": "Bot used", "value": f"{bot_name}", "inline": True},
        {"name": "Bot used", "value": bot_name, "inline": True},
        {"name": "What it did", "value": description, "inline": False},
    ]

    i = 0
    for k, v in (extra.items() if isinstance(extra, dict) else []):
        if i >= 6: break
        val = str(v)
        if len(val) > 1024:
            val = val[:1000] + "…"
        fields.append({"name": str(k), "value": val, "inline": False})
        i += 1
    # Add extra fields
    if isinstance(extra, dict):
        for k, v in extra.items():
            val = str(v)
            if len(val) > 1024:
                val = val[:1020] + "…"
            fields.append({"name": k, "value": val, "inline": False})

    embed = {
        "title": "Command Triggered",
@@ -58,17 +59,19 @@
    }
    return embed

def post_with_bot_channel(channel_id, embed):
def send_embed(channel_id, embed):
    url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"embeds": [embed]}
    resp = requests.post(url, json=payload, headers=headers, timeout=10)

    # simple rate limit handling
    if resp.status_code == 429:
        retry_after = resp.json().get("retry_after", 1)
        time.sleep(retry_after / 1000 if retry_after > 1000 else retry_after)
        retry = resp.json().get("retry_after", 1)
        time.sleep(retry / 1000)
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp
@@ -90,9 +93,8 @@
        return jsonify({"error": "missing 'command' field"}), 400

    embed = make_embed(payload)

    try:
        r = post_with_bot_channel(LOG_CHANNEL_ID, embed)
        send_embed(LOG_CHANNEL_ID, embed)
    except requests.HTTPError as e:
        return jsonify({"error": "failed to send to Discord", "details": getattr(e, "response").text if getattr(e, "response", None) else str(e)}), 500
    except Exception as e:
