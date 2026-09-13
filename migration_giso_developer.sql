-- ============================================================
--  Migratie: submodi toevoegen + /giso developer
--  Draai dit één keer in Supabase → SQL Editor → Run
--  (je hebt schema.sql al gedraaid, dit vult alleen aan)
-- ============================================================

-- 1. Kolom voor submodi (veilig als hij al bestaat)
alter table public.entries add column if not exists parent text;
create index if not exists entries_parent_idx on public.entries (parent);

-- 2. Zorg dat /giso bestaat als hoofd-command
insert into public.entries (key, title, dedicated, command_desc)
values ('giso', 'Giso', true, 'Giso-systemen')
on conflict (key) do update set dedicated = true;

-- 3. De submodus:  /giso developer
insert into public.entries
  (key, parent, title, description, url, color, links, command_desc, dedicated)
values
  (
    'giso-developer',
    'giso',
    '🟢 Giso — Developer',
    E'Your work system is **online**.\nPlease enter your password to continue.',
    'https://dev.giso.ai',
    'FEE75C',
    '[{"label": "Open dev.giso.ai", "url": "https://dev.giso.ai"}]'::jsonb,
    'Developer-omgeving openen',
    false
  )
on conflict (key) do update set
  parent       = excluded.parent,
  title        = excluded.title,
  description  = excluded.description,
  url          = excluded.url,
  color        = excluded.color,
  links        = excluded.links,
  command_desc = excluded.command_desc;
