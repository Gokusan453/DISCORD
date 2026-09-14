-- ============================================================
--  Commands:  /sleep  /wake-up  /work  /be-admin  /full-uap
--             /giso developer
--
--  Run this in Supabase -> SQL Editor -> Run
--  Then run: 2_register_commands.ps1
--  Safe to run more than once.
-- ============================================================

alter table public.entries add column if not exists parent text;
create index if not exists entries_parent_idx on public.entries (parent);

-- ------------------------------------------------------------
-- Standalone commands
-- ------------------------------------------------------------
insert into public.entries
  (key, parent, title, description, url, color, links, command_desc, dedicated)
values
  (
    'sleep', null,
    '🌙 Sleep',
    E'System is going to sleep.\n\n_Change this text with `/manage edit key:sleep field:description value:...`_',
    null, '5865F2', '[]'::jsonb,
    'Put the system to sleep', true
  ),
  (
    'wake-up', null,
    '☀️ Wake up',
    E'System is waking up.\n\n_Change this text._',
    null, 'FEE75C', '[]'::jsonb,
    'Wake the system up', true
  ),
  (
    'work', null,
    '💼 Work',
    E'Work mode.\n\n_Change this text._',
    null, '57F287', '[]'::jsonb,
    'Work mode', true
  ),
  (
    'be-admin', null,
    '🔑 Be admin',
    E'Admin mode.\n\n_Change this text._',
    null, 'ED4245', '[]'::jsonb,
    'Admin mode', true
  ),
  (
    'full-uap', null,
    '📋 Full UAP',
    E'Full UAP overview.\n\n_Change this text._',
    null, '9B59B6', '[]'::jsonb,
    'Full UAP overview', true
  )
on conflict (key) do update set
  parent    = null,
  dedicated = true;

-- ------------------------------------------------------------
-- Clean up: everything that is not one of the five commands
-- (leftovers from earlier versions: giso, app, wake, be, full)
-- ------------------------------------------------------------
delete from public.entries
where key not in ('sleep', 'wake-up', 'work', 'be-admin', 'full-uap');

-- ------------------------------------------------------------
-- Check: this is how you type each one
-- ------------------------------------------------------------
select
  key,
  case
    when parent is not null then '/' || parent || ' ' || replace(key, parent || '-', '')
    when dedicated          then '/' || key
    else '/info ' || key
  end as how_to_type,
  title
from public.entries
order by dedicated desc, key;
