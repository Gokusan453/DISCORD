"""
G's assistant — serverless Discord bot (Vercel + Supabase)

Discord stuurt elke slash command als een HTTPS POST naar dit bestand.
Geen 24/7 proces nodig, dus dit draait gratis op Vercel Hobby.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx
from fastapi import FastAPI, Request, Response
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

# ----------------------------------------------------------------------
# Config (Vercel → Settings → Environment Variables)
# ----------------------------------------------------------------------
PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
OWNER_ID = os.environ.get("OWNER_ID", "")

# Commands die de bot zelf afhandelt. Elke ANDERE commandnaam wordt
# opgezocht als 'key' in de database — dus /giso zoekt de entry 'giso'.
BUILTIN_COMMANDS = {"info", "lijst", "beheer"}

# Interaction types
PING = 1
APPLICATION_COMMAND = 2
MESSAGE_COMPONENT = 3
AUTOCOMPLETE = 4
MODAL_SUBMIT = 5

# Response types
PONG = 1
CHANNEL_MESSAGE = 4
AUTOCOMPLETE_RESULT = 8

EPHEMERAL = 64  # alleen zichtbaar voor wie het commando typte

SUB_COMMAND = 1  # option-type: submodus, bv /giso developer

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    """Eén HTTP-client die warm blijft tussen invocations."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(4.0, connect=2.0),
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
            },
        )
    return _client


# ----------------------------------------------------------------------
# Supabase (REST, geen zware SDK — scheelt koude start)
# ----------------------------------------------------------------------
async def sb_select(params: dict[str, str]) -> list[dict[str, Any]]:
    r = await get_client().get(f"{SUPABASE_URL}/rest/v1/entries", params=params)
    r.raise_for_status()
    return r.json()


async def sb_insert(row: dict[str, Any]) -> dict[str, Any]:
    r = await get_client().post(
        f"{SUPABASE_URL}/rest/v1/entries",
        json=row,
        headers={"Prefer": "return=representation"},
    )
    r.raise_for_status()
    return r.json()[0]


async def sb_update(key: str, patch: dict[str, Any]) -> list[dict[str, Any]]:
    r = await get_client().patch(
        f"{SUPABASE_URL}/rest/v1/entries",
        params={"key": f"eq.{key}"},
        json=patch,
        headers={"Prefer": "return=representation"},
    )
    r.raise_for_status()
    return r.json()


async def sb_delete(key: str) -> list[dict[str, Any]]:
    r = await get_client().delete(
        f"{SUPABASE_URL}/rest/v1/entries",
        params={"key": f"eq.{key}"},
        headers={"Prefer": "return=representation"},
    )
    r.raise_for_status()
    return r.json()


async def find_entry(term: str) -> dict[str, Any] | None:
    """Zoek op key, daarna op alias."""
    term = (term or "").strip().lower()
    if not term:
        return None

    rows = await sb_select({"key": f"eq.{term}", "enabled": "is.true", "limit": "1"})
    if rows:
        return rows[0]

    rows = await sb_select(
        {"aliases": f"cs.{{{term}}}", "enabled": "is.true", "limit": "1"}
    )
    return rows[0] if rows else None


async def bump_uses(key: str) -> None:
    try:
        await get_client().post(
            f"{SUPABASE_URL}/rest/v1/rpc/bump_uses", json={"entry_key": key}
        )
    except Exception:
        pass  # een tellertje is nooit een reden om het antwoord te laten falen


# ----------------------------------------------------------------------
# Embed bouwen
# ----------------------------------------------------------------------
def clip(text: Any, limit: int) -> str:
    s = "" if text is None else str(text)
    return s if len(s) <= limit else s[: limit - 1] + "…"


def is_http_url(value: Any) -> bool:
    return isinstance(value, str) and re.match(r"^https?://\S+$", value.strip()) is not None


def parse_color(value: Any) -> int:
    try:
        return int(str(value).lstrip("#"), 16)
    except (TypeError, ValueError):
        return 0x5865F2


def build_embed(entry: dict[str, Any]) -> dict[str, Any]:
    embed: dict[str, Any] = {
        "title": clip(entry.get("title") or entry.get("key"), 256),
        "color": parse_color(entry.get("color")),
    }

    if entry.get("description"):
        embed["description"] = clip(entry["description"], 4096)
    if is_http_url(entry.get("url")):
        embed["url"] = entry["url"]
    if is_http_url(entry.get("image_url")):
        embed["image"] = {"url": entry["image_url"]}
    if is_http_url(entry.get("thumbnail_url")):
        embed["thumbnail"] = {"url": entry["thumbnail_url"]}

    fields = entry.get("fields")
    if isinstance(fields, list) and fields:
        embed["fields"] = [
            {
                "name": clip(f.get("name", "—"), 256),
                "value": clip(f.get("value", "—"), 1024),
                "inline": bool(f.get("inline", False)),
            }
            for f in fields[:25]
            if isinstance(f, dict)
        ]

    return embed


def build_components(entry: dict[str, Any]) -> list[dict[str, Any]]:
    links = entry.get("links")
    if not isinstance(links, list):
        return []

    buttons = [
        {
            "type": 2,
            "style": 5,  # link-knop
            "label": clip(link.get("label") or "Open", 80),
            "url": link["url"].strip(),
        }
        for link in links
        if isinstance(link, dict) and is_http_url(link.get("url"))
    ][:25]

    return [
        {"type": 1, "components": buttons[i : i + 5]} for i in range(0, len(buttons), 5)
    ]


def entry_response(entry: dict[str, Any], ephemeral: bool = False) -> dict[str, Any]:
    data: dict[str, Any] = {
        "embeds": [build_embed(entry)],
        "components": build_components(entry),
    }
    if ephemeral:
        data["flags"] = EPHEMERAL
    return {"type": CHANNEL_MESSAGE, "data": data}


def text_response(message: str, ephemeral: bool = True) -> dict[str, Any]:
    data: dict[str, Any] = {"content": clip(message, 2000)}
    if ephemeral:
        data["flags"] = EPHEMERAL
    return {"type": CHANNEL_MESSAGE, "data": data}


# ----------------------------------------------------------------------
# Option-helpers
# ----------------------------------------------------------------------
def options_to_dict(options: list[dict[str, Any]] | None) -> dict[str, Any]:
    return {o["name"]: o.get("value") for o in (options or [])}


def actor_id(body: dict[str, Any]) -> str:
    member = body.get("member") or {}
    user = member.get("user") or body.get("user") or {}
    return str(user.get("id", ""))


# ----------------------------------------------------------------------
# Command handlers
# ----------------------------------------------------------------------
async def handle_info(data: dict[str, Any]) -> dict[str, Any]:
    opts = options_to_dict(data.get("options"))
    term = str(opts.get("onderwerp", "")).lower()
    # standaard privé; met publiek:true ziet het hele kanaal het
    ephemeral = not bool(opts.get("publiek", False))

    entry = await find_entry(term)
    if not entry:
        return text_response(
            f"Ik ken **{clip(term, 80)}** niet. Typ `/lijst` voor alles wat ik wél ken."
        )

    await bump_uses(entry["key"])
    return entry_response(entry, ephemeral)


async def handle_dedicated(command_name: str, data: dict[str, Any]) -> dict[str, Any]:
    # Heeft dit command een submodus? bv /giso developer  →  key 'giso-developer'
    options = data.get("options") or []
    if options and options[0].get("type") == SUB_COMMAND:
        key = f"{command_name}-{options[0]['name']}"
        options = options[0].get("options") or []
    else:
        key = command_name

    ephemeral = not bool(options_to_dict(options).get("publiek", False))

    entry = await find_entry(key)
    if not entry:
        return text_response(
            f"`/{command_name}` heeft nog geen inhoud met key `{key}`. "
            f"Voeg een rij toe in de database."
        )
    await bump_uses(entry["key"])
    return entry_response(entry, ephemeral)


async def handle_lijst() -> dict[str, Any]:
    rows = await sb_select(
        {
            "select": "key,title,command_desc,dedicated",
            "enabled": "is.true",
            "order": "key.asc",
            "limit": "100",
        }
    )
    if not rows:
        return text_response("De database is nog leeg.")

    lines = []
    for row in rows:
        prefix = f"`/{row['key']}`" if row.get("dedicated") else f"`/info {row['key']}`"
        desc = row.get("command_desc") or row.get("title") or ""
        lines.append(f"{prefix} — {clip(desc, 80)}")

    return {
        "type": CHANNEL_MESSAGE,
        "data": {
            "embeds": [
                {
                    "title": f"Alle onderwerpen ({len(rows)})",
                    "description": clip("\n".join(lines), 4096),
                    "color": 0x5865F2,
                }
            ],
            "flags": EPHEMERAL,
        },
    }


async def handle_beheer(body: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    if not OWNER_ID or actor_id(body) != OWNER_ID:
        return text_response("Alleen de eigenaar van de bot mag dit commando gebruiken.")

    sub = (data.get("options") or [{}])[0]
    action = sub.get("name")
    opts = options_to_dict(sub.get("options"))
    key = str(opts.get("key", "")).strip().lower()

    if not re.fullmatch(r"[a-z0-9_-]{1,32}", key or ""):
        return text_response(
            "Ongeldige key. Gebruik alleen kleine letters, cijfers, `-` en `_` (max 32)."
        )

    if action == "toevoegen":
        row = {
            "key": key,
            "title": opts.get("titel") or key,
            "description": opts.get("beschrijving"),
            "url": opts.get("link"),
            "image_url": opts.get("afbeelding"),
            "command_desc": clip(opts.get("beschrijving") or opts.get("titel") or key, 100),
            "dedicated": False,
        }
        try:
            await sb_insert({k: v for k, v in row.items() if v is not None})
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 409:
                return text_response(f"`{key}` bestaat al. Gebruik `/beheer bewerken`.")
            raise
        return text_response(f"Toegevoegd. Test met `/info onderwerp:{key}`", ephemeral=True)

    if action == "bewerken":
        veld = opts.get("veld")
        waarde = opts.get("waarde")
        kolommen = {
            "titel": "title",
            "beschrijving": "description",
            "link": "url",
            "afbeelding": "image_url",
            "kleur": "color",
        }
        if veld not in kolommen:
            return text_response("Onbekend veld.")
        rows = await sb_update(key, {kolommen[veld]: waarde})
        if not rows:
            return text_response(f"`{key}` bestaat niet.")
        return text_response(f"`{key}` → **{veld}** bijgewerkt.")

    if action == "knop":
        entry = await find_entry(key)
        if not entry:
            return text_response(f"`{key}` bestaat niet.")
        url = str(opts.get("url", "")).strip()
        if not is_http_url(url):
            return text_response("Die URL moet met http:// of https:// beginnen.")
        links = entry.get("links") if isinstance(entry.get("links"), list) else []
        links.append({"label": clip(opts.get("label") or "Open", 80), "url": url})
        await sb_update(key, {"links": links})
        return text_response(f"Knop toegevoegd aan `{key}` ({len(links)} knoppen).")

    if action == "verwijderen":
        rows = await sb_delete(key)
        if not rows:
            return text_response(f"`{key}` bestaat niet.")
        return text_response(f"`{key}` verwijderd.")

    return text_response("Onbekende actie.")


async def handle_autocomplete(data: dict[str, Any]) -> dict[str, Any]:
    focused = next(
        (o for o in (data.get("options") or []) if o.get("focused")),
        None,
    )
    typed = str((focused or {}).get("value", "")).strip().lower()

    params = {
        "select": "key,title",
        "enabled": "is.true",
        "order": "uses.desc,key.asc",
        "limit": "25",
    }
    if typed:
        safe = typed.replace("*", "").replace(",", "")
        params["or"] = f"(key.ilike.*{safe}*,title.ilike.*{safe}*)"

    try:
        rows = await sb_select(params)
    except Exception:
        rows = []

    return {
        "type": AUTOCOMPLETE_RESULT,
        "data": {
            "choices": [
                {"name": clip(f"{r['title']} ({r['key']})", 100), "value": r["key"]}
                for r in rows
            ]
        },
    }


# ----------------------------------------------------------------------
# Router
# ----------------------------------------------------------------------
async def route(body: dict[str, Any]) -> dict[str, Any]:
    itype = body.get("type")

    if itype == PING:
        return {"type": PONG}

    data = body.get("data") or {}
    name = data.get("name", "")

    if itype == AUTOCOMPLETE:
        return await handle_autocomplete(data)

    if itype == APPLICATION_COMMAND:
        if name == "info":
            return await handle_info(data)
        if name == "lijst":
            return await handle_lijst()
        if name == "beheer":
            return await handle_beheer(body, data)
        if name not in BUILTIN_COMMANDS:
            return await handle_dedicated(name, data)

    return text_response("Dat commando ken ik niet.")


def verify_signature(signature: str | None, timestamp: str | None, body: bytes) -> bool:
    if not (signature and timestamp and PUBLIC_KEY):
        return False
    try:
        VerifyKey(bytes.fromhex(PUBLIC_KEY)).verify(
            timestamp.encode() + body, bytes.fromhex(signature)
        )
        return True
    except (BadSignatureError, ValueError):
        return False


async def interactions(request: Request) -> Response:
    raw = await request.body()

    if not verify_signature(
        request.headers.get("x-signature-ed25519"),
        request.headers.get("x-signature-timestamp"),
        raw,
    ):
        # Discord test dit bewust bij het opslaan van de endpoint-URL.
        return Response(status_code=401, content="invalid request signature")

    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        return Response(status_code=400, content="bad json")

    try:
        payload = await route(body)
    except Exception as exc:  # nooit een 500 naar Discord teruggeven
        print(f"[error] {type(exc).__name__}: {exc}")
        payload = text_response("Er ging iets mis bij het ophalen van de gegevens.")

    return Response(
        content=json.dumps(payload),
        media_type="application/json",
        status_code=200,
    )


@app.post("/")
async def root_post(request: Request) -> Response:
    return await interactions(request)


@app.post("/api/interactions")
async def interactions_post(request: Request) -> Response:
    return await interactions(request)


@app.get("/")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "discord-interactions",
        "configured": {
            "public_key": bool(PUBLIC_KEY),
            "supabase": bool(SUPABASE_URL and SUPABASE_KEY),
            "owner": bool(OWNER_ID),
        },
    }
