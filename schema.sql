-- ============================================================
--  G's assistant  ·  Supabase schema
--  Plak dit in Supabase → SQL Editor → Run
-- ============================================================

-- ------------------------------------------------------------
-- Hoofdtabel: elk onderwerp dat de bot kan tonen
-- ------------------------------------------------------------
create table if not exists public.entries (
  id            uuid primary key default gen_random_uuid(),

  -- slug waarmee je hem opvraagt: /info onderwerp:giso  of  /giso
  key           text not null unique
                check (key ~ '^[a-z0-9_-]{1,32}$'),

  -- extra namen die naar dezelfde entry wijzen, bv. {'gizo','gsio'}
  aliases       text[] not null default '{}',

  title         text not null,
  description   text,

  -- grote klikbare titel-link van de embed
  url           text,

  -- grote afbeelding onderaan de embed
  image_url     text,
  -- kleine afbeelding rechtsboven
  thumbnail_url text,

  -- hex kleur zonder #, bv. '5865F2'
  color         text default '5865F2',

  -- knoppen onder de embed:
  -- [{"label": "Website", "url": "https://..."}, {"label": "Docs", "url": "https://..."}]
  links         jsonb not null default '[]'::jsonb,

  -- extra velden in de embed:
  -- [{"name": "Prijs", "value": "€10", "inline": true}]
  fields        jsonb not null default '[]'::jsonb,

  -- true  = krijgt een eigen slash command (/giso)
  -- false = alleen bereikbaar via /info onderwerp:...
  dedicated     boolean not null default false,

  -- submodus: verwijst naar de key van een dedicated command.
  -- key 'giso-developer' met parent 'giso'  ->  /giso developer
  parent        text,

  -- korte omschrijving die in het /giso command staat (max 100 tekens)
  command_desc  text,

  enabled       boolean not null default true,

  -- teller: hoe vaak opgevraagd
  uses          integer not null default 0,

  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create index if not exists entries_key_idx      on public.entries (key);
create index if not exists entries_enabled_idx  on public.entries (enabled);
create index if not exists entries_aliases_idx  on public.entries using gin (aliases);
create index if not exists entries_parent_idx   on public.entries (parent);

-- updated_at automatisch bijwerken
create or replace function public.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists entries_touch_updated_at on public.entries;
create trigger entries_touch_updated_at
  before update on public.entries
  for each row execute function public.touch_updated_at();

-- gebruiksteller ophogen (wordt door de bot aangeroepen)
create or replace function public.bump_uses(entry_key text)
returns void
language sql
security definer
set search_path = public
as $$
  update public.entries set uses = uses + 1 where key = entry_key;
$$;

-- ------------------------------------------------------------
-- Beveiliging
-- RLS staat AAN en er zijn GEEN publieke policies.
-- De bot praat met de service_role key en gaat daar overheen.
-- Dus: niemand kan je data lezen met de publieke anon key.
-- ------------------------------------------------------------
alter table public.entries enable row level security;

-- Publieke sleutels: geen enkele toegang
revoke all on public.entries from anon, authenticated;
revoke all on function public.bump_uses(text) from anon, authenticated;

-- De bot draait op service_role. Expliciet toekennen, zodat dit ook werkt
-- als 'Automatically expose new tables' uit staat in je projectinstellingen.
grant all on public.entries to service_role;
grant execute on function public.bump_uses(text) to service_role;

-- ============================================================
--  Voorbeelddata — pas aan of gooi weg
-- ============================================================
insert into public.entries
  (key, aliases, title, description, url, image_url, color, links, fields, dedicated, command_desc)
values
  (
    'giso',
    array['gizo'],
    'Giso',
    E'Alles wat je over Giso moet weten, op één plek.\n\nVervang deze tekst in Supabase → Table Editor → entries.',
    'https://example.com/giso',
    null,
    '5865F2',
    '[{"label": "Website",  "url": "https://example.com/giso"},
      {"label": "Handleiding", "url": "https://example.com/giso/docs"}]'::jsonb,
    '[{"name": "Status", "value": "Actief", "inline": true},
      {"name": "Versie", "value": "1.0",    "inline": true}]'::jsonb,
    true,
    'Info en links over Giso'
  ),
  (
    'app',
    array['applicatie','download'],
    'De app',
    E'Downloadlinks en info over de app.',
    'https://example.com/app',
    null,
    '57F287',
    '[{"label": "Android", "url": "https://play.google.com/"},
      {"label": "iOS",     "url": "https://apps.apple.com/"}]'::jsonb,
    '[]'::jsonb,
    true,
    'Downloadlinks en info over de app'
  )
on conflict (key) do nothing;
