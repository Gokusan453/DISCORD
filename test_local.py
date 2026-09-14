"""
Local test without Discord and without Supabase.

Sets up a fake key pair, signs test requests exactly the way Discord does,
and replaces the database calls with fixed answers.

    pip install -r requirements.txt
    python test_local.py
"""

from __future__ import annotations

import json
import os

from nacl.signing import SigningKey

# Create the key pair before app.py is imported
_signing_key = SigningKey.generate()
os.environ["DISCORD_PUBLIC_KEY"] = _signing_key.verify_key.encode().hex()
os.environ["SUPABASE_URL"] = "https://test.invalid"
os.environ["SUPABASE_SERVICE_KEY"] = "test"
os.environ["OWNER_ID"] = "42"

import app as bot  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

FAKE = {
    "sleep": {
        "key": "sleep",
        "title": "🌙 Sleep",
        "description": "System is going to sleep.",
        "color": "5865F2",
        "links": [],
        "fields": [],
    },
    "giso-developer": {
        "key": "giso-developer",
        "title": "🟢 Giso — Developer",
        "description": "Your work system is online.",
        "url": "https://dev.giso.ai",
        "image_url": "https://example.com/giso.png",
        "color": "FEE75C",
        "links": [{"label": "Open dev.giso.ai", "url": "https://dev.giso.ai"}],
    },
}


async def fake_find_entry(term):
    return FAKE.get(term)


async def fake_sb_select(params):
    return [
        {"key": "sleep", "title": "Sleep", "command_desc": "Put the system to sleep",
         "dedicated": True, "parent": None},
        {"key": "giso-developer", "title": "Giso Developer",
         "command_desc": "Open the developer environment",
         "dedicated": False, "parent": "giso"},
    ]


async def fake_bump(key):
    return None


bot.find_entry = fake_find_entry
bot.sb_select = fake_sb_select
bot.bump_uses = fake_bump

client = TestClient(bot.app)


def post(payload: dict, *, valid: bool = True):
    body = json.dumps(payload).encode()
    timestamp = "1700000000"
    signature = (
        _signing_key.sign(timestamp.encode() + body).signature.hex()
        if valid
        else "00" * 64
    )
    return client.post(
        "/api/interactions",
        content=body,
        headers={
            "X-Signature-Ed25519": signature,
            "X-Signature-Timestamp": timestamp,
            "Content-Type": "application/json",
        },
    )


def check(label: str, condition: bool) -> bool:
    print(f"{'PASS' if condition else 'FAIL'}  {label}")
    return condition


def main() -> None:
    r = []
    me = {"member": {"user": {"id": "1"}}}

    # Security
    r.append(check("bad signature -> 401", post({"type": 1}, valid=False).status_code == 401))
    resp = post({"type": 1})
    r.append(check("PING -> PONG", resp.status_code == 200 and resp.json() == {"type": 1}))

    # Standalone command
    d = post({"type": 2, "data": {"name": "sleep"}, **me}).json()["data"]
    r.append(check("/sleep -> embed", d["embeds"][0]["title"] == "🌙 Sleep"))
    r.append(check("/sleep -> private by default", d.get("flags") == 64))

    d = post({"type": 2, "data": {"name": "sleep", "options": [
        {"name": "public", "value": True}]}, **me}).json()["data"]
    r.append(check("/sleep public -> visible", "flags" not in d))

    # Sub mode
    d = post({"type": 2, "data": {"name": "giso", "options": [
        {"name": "developer", "type": 1}]}, **me}).json()["data"]
    r.append(check("/giso developer -> embed", d["embeds"][0]["url"] == "https://dev.giso.ai"))
    r.append(check("/giso developer -> button",
                   d["components"][0]["components"][0]["url"] == "https://dev.giso.ai"))
    r.append(check("/giso developer -> private by default", d.get("flags") == 64))

    d = post({"type": 2, "data": {"name": "giso", "options": [
        {"name": "developer", "type": 1, "options": [{"name": "public", "value": True}]}]},
        **me}).json()["data"]
    r.append(check("/giso developer public -> visible", "flags" not in d))

    # /info
    d = post({"type": 2, "data": {"name": "info", "options": [
        {"name": "topic", "value": "sleep"}]}, **me}).json()["data"]
    r.append(check("/info sleep -> embed", d["embeds"][0]["title"] == "🌙 Sleep"))

    d = post({"type": 2, "data": {"name": "info", "options": [
        {"name": "topic", "value": "nothing"}]}, **me}).json()["data"]
    r.append(check("unknown topic -> message", d["content"].startswith("I don't know")))

    # Autocomplete
    b = post({"type": 4, "data": {"name": "info", "options": [
        {"name": "topic", "value": "sl", "focused": True}]}}).json()
    r.append(check("autocomplete -> choices",
                   b["type"] == 8 and b["data"]["choices"][0]["value"] == "sleep"))

    # /list
    d = post({"type": 2, "data": {"name": "list"}, **me}).json()["data"]
    desc = d["embeds"][0]["description"]
    r.append(check("/list -> standalone shown as /sleep", "`/sleep`" in desc))
    r.append(check("/list -> sub mode shown as /giso developer", "`/giso developer`" in desc))

    # /manage is owner only
    d = post({"type": 2, "data": {"name": "manage", "options": [
        {"name": "delete", "options": [{"name": "key", "value": "sleep"}]}]},
        "member": {"user": {"id": "999"}}}).json()["data"]
    r.append(check("/manage by non-owner -> refused", "owner" in d["content"]))

    r.append(check("GET / -> ok", client.get("/").json()["ok"] is True))

    print()
    if all(r):
        print(f"All {len(r)} tests passed.")
    else:
        raise SystemExit(f"{r.count(False)} of {len(r)} tests failed.")


if __name__ == "__main__":
    main()
