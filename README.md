# G's assistant — Discord bot

Slash commands that pull text, links and images out of a Supabase database.

```
/sleep      /wake-up    /work
/be-admin   /full-uap   /giso developer
/info       /list       /manage
```

Runs **free** on Vercel Hobby, 24/7, with your PC switched off.

---

## How it works

A normal Discord bot is a program that stays permanently connected to Discord
(that is what discord.py does). That cannot run on Vercel, and Railway no
longer has a free tier.

So this bot uses **HTTP interactions**: Discord sends every slash command as a
signed POST to your Vercel URL, and the reply comes back in the response. No
running process, no server cost.

```
Discord  ──POST──>  Vercel (app.py)  ──REST──>  Supabase
         <─JSON───                   <────────
```

**What works:** slash commands, embeds, images, buttons, autocomplete, private
replies, knowing who ran the command and where.

**What does not:** reading normal chat messages, reacting to reactions, voice,
or showing up as "online" in the member list. None of that matters for an
info bot.

---

## Files

| File | What it does |
|---|---|
| `app.py` | The bot itself — this runs on Vercel |
| `schema.sql` | Paste into the Supabase SQL Editor once |
| `migration_commands.sql` | Adds the commands listed above |
| `commands.json` | The exact command definitions sent to Discord |
| `register_commands.py` | Registers commands (needs Python) |
| `2_register_commands.ps1` | Same thing without Python — just right-click and run |
| `1_push_to_github.bat` | Pushes your changes; Vercel redeploys itself |
| `test_local.py` | Tests everything without Discord or Supabase |

---

## Privacy and access

- **Every command is admin-only by default.** Regular members do not even see
  them in the command list. Open them up per role under
  Server Settings → Integrations.
- **Replies are private by default** — only the person who ran the command
  sees them. Add `public: true` to post one into the channel.
- **`/manage` is locked to your user ID** (`OWNER_ID`), so not even another
  admin can change your content.
- **Only you can install the app**, as long as Public Bot stays off under
  Developer Portal → Bot.

---

## Adding a topic

**From Discord** (fastest):

```
/manage add key:prices title:Prices description:Our rates link:https://...
/manage button key:prices label:Order url:https://...
```

Usable straight away with `/info topic:prices`.

**Want it as its own `/prices` command?** Set `dedicated` to `true` in the
Supabase Table Editor and run `2_register_commands.ps1` again. That is the one
step Discord cannot learn by itself — it has to be told the command name.

**From Supabase** you get more control. The columns:

| Column | Example |
|---|---|
| `key` | `sleep` — this is what you type |
| `aliases` | `{rest,off}` — alternative names |
| `title` / `description` | heading and body of the embed |
| `url` | makes the title clickable |
| `image_url` | large image at the bottom |
| `thumbnail_url` | small image top-right |
| `color` | hex without `#`, e.g. `5865F2` |
| `links` | `[{"label": "Website", "url": "https://..."}]` → buttons |
| `fields` | `[{"name": "Status", "value": "Active", "inline": true}]` |
| `dedicated` | `true` = gets its own `/command` |
| `parent` | `giso` on row `giso-developer` → `/giso developer` |

---

## Making a change

1. Edit the files in this folder
2. Double-click `1_push_to_github.bat` → Vercel redeploys in about a minute
3. Changed a command name or added a `dedicated` topic? Also run
   `2_register_commands.ps1`

---

## Testing without touching anything live

```bash
python test_local.py
```

Creates a fake key pair, signs test requests exactly the way Discord does, and
checks every command plus the security. Sixteen tests.

---

## When something breaks

**Discord refuses to save the endpoint URL**
`DISCORD_PUBLIC_KEY` in Vercel is wrong, or the deploy was not finished. Open
your Vercel URL in a browser: does it say `"public_key": true`?

**A command says "The application did not respond"**
The reply took longer than 3 seconds. Check Vercel → Logs. Usually Supabase is
paused (open the dashboard to wake it) or `SUPABASE_SERVICE_KEY` is wrong.

**"Something went wrong while fetching the data"**
The database call failed. Vercel → Logs shows the real error.

**`/manage` says only the owner may use it**
`OWNER_ID` is missing or wrong in Vercel. It is a long number, not a username.

**A new command does not show up**
Run `2_register_commands.ps1` again. Global takes up to an hour; with a server
ID it is instant.

**Error 40333 "internal network error"**
Cloudflare blocked the request because of the user agent. The scripts already
send the right one — just run it again.

---

## Costs

| | |
|---|---|
| Vercel Hobby | free, nowhere near the limits for a bot like this |
| Supabase Free | free, 500 MB — pauses after ~7 days of no activity |
| Discord | free |
