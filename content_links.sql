-- ============================================================
--  Remove the dev.giso.ai link everywhere except /work
--  Run in Supabase -> SQL Editor -> Run  (no redeploy needed)
-- ============================================================

-- /wake-up : drop button + url, change the text mention
update public.entries set
  url   = null,
  links = '[]'::jsonb,
  description =
       E'```ansi\n'
    || E'[1;37mWaking up[0m\n\n'
    || E'[1;33m▸[0m Powering on core           [1;33mdone[0m\n'
    || E'[1;33m▸[0m Restoring saved session    [1;33mdone[0m\n'
    || E'[1;33m▸[0m Syncing with local server  [1;33msynced[0m\n'
    || E'[1;33m▸[0m Reloading workspace        [1;33mready[0m\n\n'
    || E'[1;33m[██████████][0m [1;37m100%[0m\n'
    || E'```\n'
    || E'**Good to go.** ☀️  Everything is back where you left it.'
where key = 'wake-up';

-- /be-admin : drop button + url
update public.entries set url = null, links = '[]'::jsonb
where key = 'be-admin';

-- /full-uap : drop button + url (text already says "local server")
update public.entries set url = null, links = '[]'::jsonb
where key = 'full-uap';

-- /analyze : drop button + url
update public.entries set url = null, links = '[]'::jsonb
where key = 'analyze';

-- /sleep already has no link. /work keeps its link.

-- Check: only /work should still have a button
select key,
       coalesce(url, '—')          as url,
       jsonb_array_length(links)   as buttons
from public.entries
where key in ('work','sleep','wake-up','be-admin','full-uap','analyze')
order by key;
