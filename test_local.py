"""
Lokale test zonder Discord en zonder Supabase.

Zet een nep-sleutelpaar op, ondertekent testrequests precies zoals Discord dat
doet, en vervangt de database-calls door vaste antwoorden.

    pip install -r requirements.txt
    python test_local.py
"""

from __future__ import annotations

import json
import os

from nacl.signing import SigningKey

# Sleutelpaar aanmaken vóór app.py geladen wordt
_signing_key = SigningKey.generate()
os.environ["DISCORD_PUBLIC_KEY"] = _signing_key.verify_key.encode().hex()
os.environ["SUPABASE_URL"] = "https://test.invalid"
os.environ["SUPABASE_SERVICE_KEY"] = "test"
os.environ["OWNER_ID"] = "42"

import app as bot  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

FAKE = {
    "giso": {
        "key": "giso",
        "title": "Giso",
        "description": "Alles over Giso.",
        "url": "https://example.com/giso",
        "image_url": "https://example.com/giso.png",
        "color": "5865F2",
        "links": [{"label": "Website", "url": "https://example.com/giso"}],
        "fields": [{"name": "Status", "value": "Actief", "inline": True}],
    },
    "giso-developer": {
        "key": "giso-developer",
        "title": "🟢 Giso — Developer",
        "description": "Your work system is online. Please enter your password to continue.",
        "url": "https://dev.giso.ai",
        "color": "FEE75C",
        "links": [{"label": "Open dev.giso.ai", "url": "https://dev.giso.ai"}],
    },
}


async def fake_find_entry(term):
    return FAKE.get(term)


async def fake_sb_select(params):
    return [{"key": "giso", "title": "Giso", "command_desc": "Info over Giso", "dedicated": True}]


async def fake_bump(key):
    return None


bot.find_entry = fake_find_entry
bot.sb_select = fake_sb_select
bot.bump_uses = fake_bump

client = TestClient(bot.app)


def post(payload: dict, *, valid: bool = True):
    body = json.dumps(payload).encode()
    timestamp = "1700000000"
    if valid:
        signature = _signing_key.sign(timestamp.encode() + body).signature.hex()
    else:
        signature = "00" * 64
    return client.post(
        "/api/interactions",
        content=body,
        headers={
            "X-Signature-Ed25519": signature,
            "X-Signature-Timestamp": timestamp,
            "Content-Type": "application/json",
        },
    )


def check(label: str, condition: bool, detail: str = "") -> bool:
    print(f"{'PASS' if condition else 'FAIL'}  {label}{'  ' + detail if detail else ''}")
    return condition


def main() -> None:
    results = []

    # 1. Foute signature moet 401 geven (Discord test dit bij het opslaan van de URL)
    r = post({"type": 1}, valid=False)
    results.append(check("foute signature → 401", r.status_code == 401))

    # 2. PING → PONG
    r = post({"type": 1})
    results.append(check("PING → PONG", r.status_code == 200 and r.json() == {"type": 1}))

    # 3. Dedicated command /giso
    r = post({"type": 2, "data": {"name": "giso"}, "member": {"user": {"id": "1"}}})
    data = r.json()["data"]
    embed = data["embeds"][0]
    results.append(check("/giso → embed", embed["title"] == "Giso"))
    results.append(check("/giso → afbeelding", embed["image"]["url"].endswith(".png")))
    results.append(
        check("/giso → linkknop", data["components"][0]["components"][0]["style"] == 5)
    )

    # 3b. Submodus /giso developer
    r = post(
        {
            "type": 2,
            "data": {"name": "giso", "options": [{"name": "developer", "type": 1}]},
            "member": {"user": {"id": "1"}},
        }
    )
    dev = r.json()["data"]
    results.append(check("/giso developer → embed", dev["embeds"][0]["url"] == "https://dev.giso.ai"))
    results.append(
        check("/giso developer → knop", dev["components"][0]["components"][0]["url"] == "https://dev.giso.ai")
    )
    results.append(check("/giso developer → standaard privé", dev.get("flags") == 64))

    # 3c. Submodus met publiek:true → wel zichtbaar voor iedereen
    r = post(
        {
            "type": 2,
            "data": {
                "name": "giso",
                "options": [
                    {"name": "developer", "type": 1, "options": [{"name": "publiek", "value": True}]}
                ],
            },
            "member": {"user": {"id": "1"}},
        }
    )
    results.append(check("/giso developer publiek → zichtbaar", "flags" not in r.json()["data"]))

    # 3d. /giso zonder publiek → privé
    r = post({"type": 2, "data": {"name": "giso"}, "member": {"user": {"id": "1"}}})
    results.append(check("/giso → standaard privé", r.json()["data"].get("flags") == 64))

    # 4. /info met bestaand onderwerp
    r = post(
        {
            "type": 2,
            "data": {"name": "info", "options": [{"name": "onderwerp", "value": "giso"}]},
            "member": {"user": {"id": "1"}},
        }
    )
    results.append(check("/info giso → embed", r.json()["data"]["embeds"][0]["title"] == "Giso"))

    # 5. /info publiek:true → zichtbaar voor het hele kanaal
    r = post(
        {
            "type": 2,
            "data": {
                "name": "info",
                "options": [
                    {"name": "onderwerp", "value": "giso"},
                    {"name": "publiek", "value": True},
                ],
            },
            "member": {"user": {"id": "1"}},
        }
    )
    results.append(check("/info publiek → zichtbaar", "flags" not in r.json()["data"]))

    # 6. Onbekend onderwerp → nette melding, geen crash
    r = post(
        {
            "type": 2,
            "data": {"name": "info", "options": [{"name": "onderwerp", "value": "bestaatniet"}]},
            "member": {"user": {"id": "1"}},
        }
    )
    content = r.json()["data"]["content"]
    results.append(
        check(
            "onbekend onderwerp → melding",
            content.startswith("Ik ken") and r.json()["data"]["flags"] == 64,
        )
    )

    # 7. Autocomplete
    r = post(
        {
            "type": 4,
            "data": {"name": "info", "options": [{"name": "onderwerp", "value": "gi", "focused": True}]},
        }
    )
    body = r.json()
    results.append(
        check("autocomplete → keuzes", body["type"] == 8 and body["data"]["choices"][0]["value"] == "giso")
    )

    # 8. /lijst
    r = post({"type": 2, "data": {"name": "lijst"}, "member": {"user": {"id": "1"}}})
    results.append(check("/lijst → overzicht", "/giso" in r.json()["data"]["embeds"][0]["description"]))

    # 9. Beheer door een vreemde → geweigerd
    r = post(
        {
            "type": 2,
            "data": {"name": "beheer", "options": [{"name": "verwijderen", "options": [{"name": "key", "value": "giso"}]}]},
            "member": {"user": {"id": "999"}},
        }
    )
    results.append(check("beheer door niet-eigenaar → geweigerd", "eigenaar" in r.json()["data"]["content"]))

    # 10. Health check
    results.append(check("GET / → ok", client.get("/").json()["ok"] is True))

    print()
    if all(results):
        print(f"Alle {len(results)} tests geslaagd.")
    else:
        print(f"{results.count(False)} van {len(results)} tests gefaald.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
