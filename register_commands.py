"""
Registers the slash commands with Discord.

Run this locally (or via GitHub Actions) whenever you:
  - mark a new topic as `dedicated = true` in Supabase
  - change a command description

Usage:
    python register_commands.py                 # global (can take up to an hour)
    python register_commands.py --guild 1234..  # one server, visible instantly
    python register_commands.py --list          # show what is registered now
"""

from __future__ import annotations

import argparse
import os
import re
import sys

import httpx

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
APP_ID = os.environ.get("DISCORD_APP_ID", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

API = "https://discord.com/api/v10"

# Discord and Cloudflare block browser-like user agents (error 40333).
USER_AGENT = "DiscordBot (https://github.com/Gokusan453/DISCORD, 1.0)"

# Option types
STRING, BOOLEAN, SUB_COMMAND = 3, 5, 1

VALID_NAME = re.compile(r"^[a-z0-9_-]{1,32}$")

# "0" = hidden from everyone except server administrators by default.
# You can still open it up per role via Server Settings → Integrations.
ADMIN_ONLY = "0"

# Replies are private by default; this switch posts one to the channel.
PUBLIC = {
    "type": BOOLEAN,
    "name": "public",
    "description": "Show the reply to everyone in the channel",
    "required": False,
}

RESERVED = {"info", "list", "manage"}


def base_commands() -> list[dict]:
    return [
        {
            "name": "info",
            "description": "Info, links and images about a topic",
            "default_member_permissions": ADMIN_ONLY,
            "options": [
                {
                    "type": STRING,
                    "name": "topic",
                    "description": "What do you want info about? (type to search)",
                    "required": True,
                    "autocomplete": True,
                },
                PUBLIC,
            ],
        },
        {
            "name": "list",
            "description": "Show every topic I know",
            "default_member_permissions": ADMIN_ONLY,
        },
        {
            "name": "manage",
            "description": "Manage the content (owner only)",
            "default_member_permissions": ADMIN_ONLY,
            "options": [
                {
                    "type": SUB_COMMAND,
                    "name": "add",
                    "description": "Add a new topic",
                    "options": [
                        {"type": STRING, "name": "key", "description": "Short name, e.g. sleep", "required": True},
                        {"type": STRING, "name": "title", "description": "Title of the embed", "required": True},
                        {"type": STRING, "name": "description", "description": "Body text", "required": False},
                        {"type": STRING, "name": "link", "description": "Main link (https://...)", "required": False},
                        {"type": STRING, "name": "image", "description": "Image URL (https://...)", "required": False},
                    ],
                },
                {
                    "type": SUB_COMMAND,
                    "name": "edit",
                    "description": "Change one field of a topic",
                    "options": [
                        {"type": STRING, "name": "key", "description": "Which topic?", "required": True},
                        {
                            "type": STRING,
                            "name": "field",
                            "description": "What do you want to change?",
                            "required": True,
                            "choices": [
                                {"name": "title", "value": "title"},
                                {"name": "description", "value": "description"},
                                {"name": "link", "value": "link"},
                                {"name": "image", "value": "image"},
                                {"name": "color (hex, e.g. 5865F2)", "value": "color"},
                            ],
                        },
                        {"type": STRING, "name": "value", "description": "New value", "required": True},
                    ],
                },
                {
                    "type": SUB_COMMAND,
                    "name": "button",
                    "description": "Add a link button under the embed",
                    "options": [
                        {"type": STRING, "name": "key", "description": "Which topic?", "required": True},
                        {"type": STRING, "name": "label", "description": "Text on the button", "required": True},
                        {"type": STRING, "name": "url", "description": "https://...", "required": True},
                    ],
                },
                {
                    "type": SUB_COMMAND,
                    "name": "delete",
                    "description": "Delete a topic",
                    "options": [
                        {"type": STRING, "name": "key", "description": "Which topic?", "required": True},
                    ],
                },
            ],
        },
    ]


def _fetch(params: dict) -> list[dict]:
    r = httpx.get(
        f"{SUPABASE_URL}/rest/v1/entries",
        params=params,
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def dedicated_commands() -> list[dict]:
    """
    Every topic with dedicated = true gets its own /command.
    If such a topic has children (rows with parent = <key>), those become
    sub modes: key 'giso' + child 'giso-developer'  ->  /giso developer
    """
    if not (SUPABASE_URL and SUPABASE_KEY):
        print("! Supabase not configured — registering base commands only.")
        return []

    parents = _fetch(
        {
            "select": "key,title,command_desc",
            "dedicated": "is.true",
            "enabled": "is.true",
            "order": "key.asc",
        }
    )
    children = _fetch(
        {
            "select": "key,title,command_desc,parent",
            "parent": "not.is.null",
            "enabled": "is.true",
            "order": "key.asc",
        }
    )

    by_parent: dict[str, list[dict]] = {}
    for c in children:
        by_parent.setdefault(c["parent"], []).append(c)

    commands = []
    for row in parents:
        key = row["key"]
        if not VALID_NAME.match(key):
            print(f"! skipped '{key}': invalid command name.")
            continue
        if key in RESERVED:
            print(f"! skipped '{key}': that name is already taken.")
            continue

        desc = (row.get("command_desc") or row.get("title") or key)[:100]
        kids = by_parent.get(key, [])

        if kids:
            subs = []
            for c in kids[:25]:
                mode = c["key"]
                if mode.startswith(key + "-"):
                    mode = mode[len(key) + 1 :]
                if not VALID_NAME.match(mode):
                    print(f"! skipped sub mode '{c['key']}': invalid name.")
                    continue
                subs.append(
                    {
                        "type": SUB_COMMAND,
                        "name": mode,
                        "description": (c.get("command_desc") or c.get("title") or mode)[:100],
                        "options": [PUBLIC],
                    }
                )
            commands.append(
                {
                    "name": key,
                    "description": desc,
                    "default_member_permissions": ADMIN_ONLY,
                    "options": subs,
                }
            )
        else:
            commands.append(
                {
                    "name": key,
                    "description": desc,
                    "default_member_permissions": ADMIN_ONLY,
                    "options": [PUBLIC],
                }
            )
    return commands


def endpoint(guild: str | None) -> str:
    if guild:
        return f"{API}/applications/{APP_ID}/guilds/{guild}/commands"
    return f"{API}/applications/{APP_ID}/commands"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--guild", help="Server ID: commands appear instantly")
    parser.add_argument("--list", action="store_true", help="Show current commands")
    args = parser.parse_args()

    if not (TOKEN and APP_ID):
        print("DISCORD_BOT_TOKEN and DISCORD_APP_ID must be set in .env")
        return 1

    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    url = endpoint(args.guild)

    if args.list:
        r = httpx.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        for c in r.json():
            print(f"  /{c['name']} — {c.get('description', '')}")
        return 0

    payload = base_commands() + dedicated_commands()

    r = httpx.put(url, headers=headers, json=payload, timeout=30)
    if r.status_code >= 400:
        print(f"Discord returned {r.status_code}:\n{r.text}")
        return 1

    scope = f"server {args.guild}" if args.guild else "all servers (global)"
    print(f"Registered {len(r.json())} commands for {scope}:")
    for c in r.json():
        print(f"  /{c['name']} — {c.get('description', '')}")
    if not args.guild:
        print("\nGlobal commands can take up to an hour to appear everywhere.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
