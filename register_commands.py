"""
Registreert de slash commands bij Discord.

Draai dit lokaal (of via GitHub Actions) telkens als je:
  - een nieuw onderwerp `dedicated = true` maakt in Supabase
  - de omschrijving van een command verandert

Gebruik:
    python register_commands.py                 # globaal (kan tot 1 uur duren)
    python register_commands.py --guild 1234..  # in 1 server, meteen zichtbaar
    python register_commands.py --list          # laat zien wat er nu geregistreerd staat
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

# Option types
STRING, BOOLEAN, SUB_COMMAND = 3, 5, 1

VALID_NAME = re.compile(r"^[a-z0-9_-]{1,32}$")


def base_commands() -> list[dict]:
    return [
        {
            "name": "info",
            "description": "Info, links en afbeeldingen over een onderwerp",
            "options": [
                {
                    "type": STRING,
                    "name": "onderwerp",
                    "description": "Waar wil je info over? (typ om te zoeken)",
                    "required": True,
                    "autocomplete": True,
                },
                {
                    "type": BOOLEAN,
                    "name": "prive",
                    "description": "Alleen jij ziet het antwoord",
                    "required": False,
                },
            ],
        },
        {
            "name": "lijst",
            "description": "Laat alle onderwerpen zien die ik ken",
        },
        {
            "name": "beheer",
            "description": "Inhoud beheren (alleen de eigenaar)",
            "default_member_permissions": "0",
            "options": [
                {
                    "type": SUB_COMMAND,
                    "name": "toevoegen",
                    "description": "Nieuw onderwerp toevoegen",
                    "options": [
                        {"type": STRING, "name": "key", "description": "Korte naam, bv. giso", "required": True},
                        {"type": STRING, "name": "titel", "description": "Titel van de embed", "required": True},
                        {"type": STRING, "name": "beschrijving", "description": "Tekst", "required": False},
                        {"type": STRING, "name": "link", "description": "Hoofdlink (https://...)", "required": False},
                        {"type": STRING, "name": "afbeelding", "description": "Afbeeldings-URL (https://...)", "required": False},
                    ],
                },
                {
                    "type": SUB_COMMAND,
                    "name": "bewerken",
                    "description": "Eén veld van een onderwerp aanpassen",
                    "options": [
                        {"type": STRING, "name": "key", "description": "Welk onderwerp?", "required": True},
                        {
                            "type": STRING,
                            "name": "veld",
                            "description": "Wat wil je aanpassen?",
                            "required": True,
                            "choices": [
                                {"name": "titel", "value": "titel"},
                                {"name": "beschrijving", "value": "beschrijving"},
                                {"name": "link", "value": "link"},
                                {"name": "afbeelding", "value": "afbeelding"},
                                {"name": "kleur (hex, bv. 5865F2)", "value": "kleur"},
                            ],
                        },
                        {"type": STRING, "name": "waarde", "description": "Nieuwe waarde", "required": True},
                    ],
                },
                {
                    "type": SUB_COMMAND,
                    "name": "knop",
                    "description": "Een linkknop onder de embed toevoegen",
                    "options": [
                        {"type": STRING, "name": "key", "description": "Welk onderwerp?", "required": True},
                        {"type": STRING, "name": "label", "description": "Tekst op de knop", "required": True},
                        {"type": STRING, "name": "url", "description": "https://...", "required": True},
                    ],
                },
                {
                    "type": SUB_COMMAND,
                    "name": "verwijderen",
                    "description": "Onderwerp verwijderen",
                    "options": [
                        {"type": STRING, "name": "key", "description": "Welk onderwerp?", "required": True},
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
    Elk onderwerp met dedicated = true krijgt een eigen /commando.
    Heeft zo'n onderwerp kinderen (rijen met parent = <key>), dan worden dat
    submodi:  key 'giso' + kind 'giso-developer'  ->  /giso developer
    """
    if not (SUPABASE_URL and SUPABASE_KEY):
        print("! Supabase niet geconfigureerd — alleen de basiscommando's worden geregistreerd.")
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
            print(f"! '{key}' overgeslagen: ongeldige commandnaam.")
            continue
        if key in {"info", "lijst", "beheer"}:
            print(f"! '{key}' overgeslagen: die naam is al in gebruik.")
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
                    print(f"! modus '{c['key']}' overgeslagen: ongeldige naam.")
                    continue
                subs.append(
                    {
                        "type": SUB_COMMAND,
                        "name": mode,
                        "description": (c.get("command_desc") or c.get("title") or mode)[:100],
                    }
                )
            commands.append({"name": key, "description": desc, "options": subs})
        else:
            commands.append({"name": key, "description": desc})
    return commands


def endpoint(guild: str | None) -> str:
    if guild:
        return f"{API}/applications/{APP_ID}/guilds/{guild}/commands"
    return f"{API}/applications/{APP_ID}/commands"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--guild", help="Server-ID: commands zijn dan meteen zichtbaar")
    parser.add_argument("--list", action="store_true", help="Toon huidige commands")
    args = parser.parse_args()

    if not (TOKEN and APP_ID):
        print("DISCORD_BOT_TOKEN en DISCORD_APP_ID moeten in .env staan.")
        return 1

    headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}
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
        print(f"Discord gaf {r.status_code}:\n{r.text}")
        return 1

    scope = f"server {args.guild}" if args.guild else "alle servers (globaal)"
    print(f"{len(r.json())} commands geregistreerd voor {scope}:")
    for c in r.json():
        print(f"  /{c['name']} — {c.get('description', '')}")
    if not args.guild:
        print("\nGlobale commands kunnen tot een uur duren voor ze overal zichtbaar zijn.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
