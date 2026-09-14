-- ============================================================
--  G's assistant  ·  Supabase schema
--  Paste this into Supabase -> SQL Editor -> Run
-- ============================================================

-- ------------------------------------------------------------
-- Main table: every topic the bot can show
-- ------------------------------------------------------------
create table if not exists public.entries (
  id            uuid primary key default gen_random_uuid(),

  -- the slug you type: /info topic:sleep  or  /sleep
  key           text not null unique
                check (key ~ '^[a-z0-9_-]{1,32}$'),

  -- extra names pointing at the same entry, e.g. {'rest','off'}
  aliases       text[] not null default '{}',

  title         text not null,
  description   text,

  -- makes the embed title clickable
  url           text,

  -- large image at the bottom of the embed
  image_url     text,
  -- small image in the top-right corner
  thumbnail_url text,

  -- hex color without the #, e.g. '5865F2'
  color         text default '5865F2',

  -- buttons under the embed:
  -- [{"label": "Website", "url": "https://..."}, {"label": "Docs", "url": "https://..."}]
  links         jsonb not null default '[]'::jsonb,

  -- extra fields inside the embed:
  -- [{"name": "Status", "value": "Active", "inline": true}]
  fields        jsonb not null default '[]'::jsonb,

  -- true  = gets its own slash command (/sleep)
  -- false = only reachable through /info topic:...
  dedicated     boolean not null default false,

  -- sub mode: points at the key of a dedicated command.
  -- key 'giso-developer' with parent 'giso'  ->  /giso developer
  parent        text,

  -- short text shown in the command list (max 100 characters)
  command_desc  text,

  enabled       boolean not null default true,

  -- counter: how often it has been requested
  uses          integer not null default 0,

  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create index if not exists entries_key_idx      on public.entries (key);
create index if not exists entries_enabled_idx  on public.entries (enabled);
create index if not exists entries_aliases_idx  on public.entries using gin (aliases);
create index if not exists entries_parent_idx   on public.entries (parent);

-- keep updated_at current automatically
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

-- increment the usage counter (called by the bot)
create or replace function public.bump_uses(entry_key text)
returns void
language sql
security definer
set search_path = public
as $$
  update public.entries set uses = uses + 1 where key = entry_key;
$$;

-- ------------------------------------------------------------
-- Security
-- RLS is ON and there are NO public policies.
-- The bot talks to the database with the service_role key, which
-- bypasses RLS. So nobody can read your data with the public key.
-- ------------------------------------------------------------
alter table public.entries enable row level security;

-- public keys: no access at all
revoke all on public.entries from anon, authenticated;
revoke all on function public.bump_uses(text) from anon, authenticated;

-- the bot runs as service_role. Granted explicitly so this keeps working
-- even if 'Automatically expose new tables' is turned off in your settings.
grant all on public.entries to service_role;
grant execute on function public.bump_uses(text) to service_role;

-- ============================================================
--  Next step: run migration_commands.sql to add the commands
-- ============================================================
