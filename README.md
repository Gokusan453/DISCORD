# G's assistant — Discord bot

Slash commands die info, links en afbeeldingen uit een Supabase-database halen.

```
/giso              →  embed met tekst, afbeelding en knoppen
/app               →  hetzelfde, ander onderwerp
/info onderwerp:…  →  één commando met zoek-autocomplete voor álles
/lijst             →  overzicht van alle onderwerpen
/beheer …          →  onderwerpen toevoegen/aanpassen vanuit Discord (alleen jij)
```

Draait **gratis** op Vercel Hobby, 24/7, zonder dat je pc aan hoeft.

---

## Hoe het werkt

Een normale Discord-bot is een programma dat permanent verbonden blijft met Discord
(dat is wat discord.py doet). Dat kan niet op Vercel, en Railway heeft geen gratis
tier meer.

Deze bot werkt daarom via **HTTP interactions**: Discord stuurt elke slash command
als een beveiligde POST naar jouw Vercel-URL, en het antwoord komt terug in de
response. Geen draaiend proces, dus geen serverkosten.

```
Discord  ──POST──>  Vercel (app.py)  ──REST──>  Supabase
         <─JSON───                   <────────
```

Wat hiermee **wel** kan: slash commands, embeds, afbeeldingen, knoppen, autocomplete,
privé-antwoorden, gebruikers en servers herkennen.

Wat **niet** kan: gewone chatberichten meelezen, reageren op reacties, voice, of als
"online" in de ledenlijst staan. Voor een info-bot maakt dat niets uit.

---

## Bestanden

| Bestand | Wat het doet |
|---|---|
| `app.py` | De bot zelf — dit draait op Vercel |
| `schema.sql` | Plak je één keer in de Supabase SQL Editor |
| `register_commands.py` | Meldt je slash commands aan bij Discord |
| `test_local.py` | Test alles zonder Discord of Supabase |
| `.env.example` | Kopieer naar `.env` en vul in |

---

## Stap 1 — Supabase

In het scherm dat je open had staan:

- **Organization**: AL (Free)
- **Project name**: `dc al`
- **Region**: Europe (West EU / Ierland) ← de bot draait in Vercel-regio `dub1`, ernaast
- **Enable Data API**: **aan** (de bot praat via de REST API)
- **Automatically expose new tables**: mag uit, maakt niet uit — `schema.sql` zet RLS
  aan en trekt alle rechten van `anon` in, dus je data is sowieso niet publiek leesbaar
- **Enable automatic RLS**: aanzetten is prima

Bewaar het database-wachtwoord ergens veilig (je hebt het voor deze bot niet nodig,
maar je krijgt het maar één keer te zien).

Als het project klaar is:

1. **SQL Editor** → **New query** → plak de complete inhoud van `schema.sql` → **Run**.
   Je ziet daarna twee voorbeeldrijen in **Table Editor → entries**.
2. **Project Settings → Data API** → kopieer de **Project URL**.
3. **Project Settings → API Keys** → kopieer de **`service_role`** key.
   Dit is een geheime sleutel die om alle beveiliging heen gaat: alleen in
   Vercel-environment-variabelen en in je lokale `.env`, nooit in GitHub.

> Let op: gratis Supabase-projecten gaan in de pauzestand na ±7 dagen zonder
> activiteit. Zolang de bot af en toe gebruikt wordt, gebeurt dat niet.

---

## Stap 2 — Discord

Op https://discord.com/developers/applications → **G's assistant**:

1. **Bot** → **Reset Token** → kopieer het token. Ook geheim.
2. **General Information** → Application ID en Public Key staan al ingevuld in
   `.env.example`.
3. Je eigen user-ID: Discord → Instellingen → Geavanceerd → **Ontwikkelaarsmodus aan**,
   dan rechtsklik op jezelf → **Copy User ID**. Dat wordt `OWNER_ID`.
4. Voeg de app toe aan je server:
   https://discord.com/oauth2/authorize?client_id=1548832028055838780&scope=applications.commands

---

## Stap 3 — Naar GitHub en Vercel

```bash
cd discord-bot
git init
git add .
git commit -m "Discord bot"
git branch -M main
git remote add origin https://github.com/JOUW-NAAM/discord-bot.git
git push -u origin main
```

`.env` staat in `.gitignore`, dus je sleutels gaan niet mee. Controleer dat.

Op https://vercel.com → **Add New → Project** → je repo importeren.
Vercel herkent Python automatisch; je hoeft niets in te stellen behalve
**Environment Variables** (kies *All Environments*):

| Naam | Waarde |
|---|---|
| `DISCORD_PUBLIC_KEY` | `55d9c3fb00fcbfb5e7be60e1a65faf798fdc0e91876051fccdb84366e57f3700` |
| `SUPABASE_URL` | `https://xxxx.supabase.co` |
| `SUPABASE_SERVICE_KEY` | je service_role key |
| `OWNER_ID` | jouw Discord user-ID |

Deploy. Open daarna je URL in de browser — je hoort
`{"ok": true, ...}` te zien met overal `true` achter.

---

## Stap 4 — Endpoint koppelen

Terug in het Discord Developer Portal, in het veld dat je al op je scherm had:

**Interactions Endpoint URL** → `https://jouw-project.vercel.app/api/interactions`

→ **Save Changes**. Discord stuurt meteen een testbericht met een expres foute
handtekening; slaat hij op, dan werkt de koppeling. Krijg je een foutmelding, kijk
dan onderaan bij *Als er iets misgaat*.

---

## Stap 5 — Commands registreren

Lokaal (eenmalig Python nodig):

```bash
pip install -r requirements.txt
cp .env.example .env      # vul DISCORD_BOT_TOKEN, OWNER_ID en de Supabase-gegevens in
python register_commands.py --guild JOUW_SERVER_ID
```

Met `--guild` zijn de commands **direct** zichtbaar in die ene server — ideaal om te
testen. Server-ID krijg je met rechtsklik op de servernaam → Copy Server ID.

Werkt alles? Dan voor alle servers:

```bash
python register_commands.py
```

Globale commands kunnen tot een uur duren voor ze overal doorkomen.

---

## Een nieuw onderwerp toevoegen

**Vanuit Discord** (snelst):

```
/beheer toevoegen key:prijzen titel:Prijzen beschrijving:Onze tarieven link:https://...
/beheer knop key:prijzen label:Bestellen url:https://...
```

Meteen bruikbaar met `/info onderwerp:prijzen`.

**Wil je er een eigen `/prijzen` command van maken?** Zet `dedicated` op `true` in de
Table Editor en draai `python register_commands.py` opnieuw. Dat is de enige stap die
niet vanuit Discord kan — Discord moet de commandnaam kennen.

**Vanuit Supabase** heb je meer controle. De kolommen:

| Kolom | Voorbeeld |
|---|---|
| `key` | `giso` — dit typ je |
| `aliases` | `{gizo,gso}` — alternatieve namen |
| `title` / `description` | kop en tekst van de embed |
| `url` | maakt de titel klikbaar |
| `image_url` | grote afbeelding onderaan |
| `thumbnail_url` | kleine afbeelding rechtsboven |
| `color` | hexkleur zonder `#`, bv. `5865F2` |
| `links` | `[{"label": "Website", "url": "https://..."}]` → knoppen |
| `fields` | `[{"name": "Prijs", "value": "€10", "inline": true}]` |
| `dedicated` | `true` = krijgt een eigen `/commando` |

---

## Testen zonder alles op te zetten

```bash
python test_local.py
```

Dit maakt een nep-sleutelpaar aan, ondertekent testrequests precies zoals Discord
dat doet, en controleert alle commands plus de beveiliging. Twaalf tests, allemaal
groen in deze versie.

---

## Als er iets misgaat

**Discord weigert de endpoint-URL op te slaan**
De `DISCORD_PUBLIC_KEY` in Vercel klopt niet, of de deploy was nog niet klaar. Check
je Vercel-URL in de browser: staat er `"public_key": true`?

**Command geeft "De applicatie reageerde niet"**
Het antwoord duurde langer dan 3 seconden. Kijk in Vercel → Logs. Meestal staat
Supabase in de pauzestand (open je Supabase-dashboard om hem te wekken) of klopt
`SUPABASE_SERVICE_KEY` niet.

**"Er ging iets mis bij het ophalen van de gegevens"**
De database-call faalde. Vercel → Logs toont de echte fout.

**`/beheer` zegt dat alleen de eigenaar dit mag**
`OWNER_ID` staat niet of verkeerd in Vercel. Het is een lang getal, geen gebruikersnaam.

**Nieuw `/commando` verschijnt niet**
`register_commands.py` opnieuw draaien. Globaal kan tot een uur duren; met `--guild` is
het direct.

---

## Kosten

| | |
|---|---|
| Vercel Hobby | gratis, ruim binnen de limieten voor een bot als deze |
| Supabase Free | gratis, 500 MB database — pauzeert na ±7 dagen niets doen |
| Discord | gratis |
