-- ============================================================
--  Styled "system readout" content for all five commands.
--  Run in Supabase -> SQL Editor -> Run.
--  Takes effect immediately, no redeploy needed.
--
--  The green/coloured text comes from Discord ```ansi code blocks.
-- ============================================================

-- ------------------------------------------------------------
-- /work   —  green, workspace boot
-- ------------------------------------------------------------
update public.entries set
  title = '⚙️  WORK MODE',
  color = '57F287',
  url   = 'https://dev.giso.ai',
  description =
       E'```ansi\n'
    || E'[1;37mBooting workspace[0m\n\n'
    || E'[1;32m▸[0m Starting system            [1;32mdone[0m\n'
    || E'[1;32m▸[0m Loading modules            [1;32mdone[0m\n'
    || E'[1;32m▸[0m Connecting to dev.giso.ai  [1;32monline[0m\n'
    || E'[1;32m▸[0m Running analysis           [1;32mcomplete[0m\n'
    || E'[1;32m▸[0m Sending report to phone    [1;32msent[0m\n\n'
    || E'[1;32m[██████████][0m [1;37m100%[0m\n'
    || E'```\n'
    || E'**All systems ready.** 🚀',
  links  = '[{"label": "Open dev.giso.ai", "url": "https://dev.giso.ai"}]'::jsonb,
  fields = E'[
      {"name": "Status",   "value": "🟢 Online",   "inline": true},
      {"name": "Analysis", "value": "✅ Complete", "inline": true},
      {"name": "Phone",    "value": "📲 Notified", "inline": true}
    ]'::jsonb,
  command_desc = 'Start the workspace'
where key = 'work';

-- ------------------------------------------------------------
-- /sleep  —  blue, powering down
-- ------------------------------------------------------------
update public.entries set
  title = '🌙  SLEEP MODE',
  color = '5865F2',
  url   = null,
  description =
       E'```ansi\n'
    || E'[1;37mPowering down[0m\n\n'
    || E'[1;34m▸[0m Saving current state       [1;34mdone[0m\n'
    || E'[1;34m▸[0m Closing active modules     [1;34mdone[0m\n'
    || E'[1;34m▸[0m Pausing background tasks   [1;34mdone[0m\n'
    || E'[1;34m▸[0m Entering low-power mode    [1;34mok[0m\n\n'
    || E'[1;34m[██████████][0m [1;37m100%[0m\n'
    || E'```\n'
    || E'**System is now asleep.** 😴  Use `/wake-up` to resume.',
  links  = '[]'::jsonb,
  fields = E'[
      {"name": "Status",  "value": "🔵 Sleeping",  "inline": true},
      {"name": "State",   "value": "💾 Saved",      "inline": true},
      {"name": "Power",   "value": "🌙 Low",        "inline": true}
    ]'::jsonb,
  command_desc = 'Put the system to sleep'
where key = 'sleep';

-- ------------------------------------------------------------
-- /wake-up   —  yellow, waking
-- ------------------------------------------------------------
update public.entries set
  title = '☀️  WAKE UP',
  color = 'FEE75C',
  url   = 'https://dev.giso.ai',
  description =
       E'```ansi\n'
    || E'[1;37mWaking up[0m\n\n'
    || E'[1;33m▸[0m Powering on core           [1;33mdone[0m\n'
    || E'[1;33m▸[0m Restoring saved session    [1;33mdone[0m\n'
    || E'[1;33m▸[0m Syncing with dev.giso.ai   [1;33msynced[0m\n'
    || E'[1;33m▸[0m Reloading workspace        [1;33mready[0m\n\n'
    || E'[1;33m[██████████][0m [1;37m100%[0m\n'
    || E'```\n'
    || E'**Good to go.** ☀️  Everything is back where you left it.',
  links  = '[{"label": "Open dev.giso.ai", "url": "https://dev.giso.ai"}]'::jsonb,
  fields = E'[
      {"name": "Status",  "value": "🟢 Awake",     "inline": true},
      {"name": "Session", "value": "♻️ Restored",  "inline": true},
      {"name": "Sync",    "value": "🔗 Synced",    "inline": true}
    ]'::jsonb,
  command_desc = 'Wake the system up'
where key = 'wake-up';

-- ------------------------------------------------------------
-- /be-admin   —  red, privilege elevation
-- ------------------------------------------------------------
update public.entries set
  title = '🔑  ADMIN ACCESS',
  color = 'ED4245',
  url   = 'https://dev.giso.ai',
  description =
       E'```ansi\n'
    || E'[1;37mElevating privileges[0m\n\n'
    || E'[1;31m▸[0m Verifying identity         [1;31mok[0m\n'
    || E'[1;31m▸[0m Requesting elevation       [1;31mgranted[0m\n'
    || E'[1;31m▸[0m Unlocking admin panel      [1;31mopen[0m\n'
    || E'[1;31m▸[0m Loading controls           [1;31mready[0m\n\n'
    || E'[1;31m[██████████][0m [1;37m100%[0m\n'
    || E'```\n'
    || E'**Admin mode active.** 🔓  Full control unlocked.',
  links  = '[{"label": "Open admin panel", "url": "https://dev.giso.ai"}]'::jsonb,
  fields = E'[
      {"name": "Role",   "value": "🔴 Admin",     "inline": true},
      {"name": "Access", "value": "🔓 Full",      "inline": true},
      {"name": "Panel",  "value": "🖥️ Open",      "inline": true}
    ]'::jsonb,
  command_desc = 'Enter admin mode'
where key = 'be-admin';

-- ------------------------------------------------------------
-- /full-uap   —  purple, full report
-- ------------------------------------------------------------
update public.entries set
  title = '📋  FULL UAP',
  color = '9B59B6',
  url   = 'https://dev.giso.ai',
  description =
       E'```ansi\n'
    || E'[1;37mGenerating full report[0m\n\n'
    || E'[1;35m▸[0m Collecting data            [1;35mdone[0m\n'
    || E'[1;35m▸[0m Compiling overview         [1;35mdone[0m\n'
    || E'[1;35m▸[0m Rendering report           [1;35mdone[0m\n'
    || E'[1;35m▸[0m Uploading to dev.giso.ai   [1;35mready[0m\n\n'
    || E'[1;35m[██████████][0m [1;37m100%[0m\n'
    || E'```\n'
    || E'**Full UAP overview is ready.** 📊',
  links  = '[{"label": "View full report", "url": "https://dev.giso.ai"}]'::jsonb,
  fields = E'[
      {"name": "Report",  "value": "📋 Complete",  "inline": true},
      {"name": "Records", "value": "📊 All",       "inline": true},
      {"name": "Export",  "value": "⬆️ Ready",     "inline": true}
    ]'::jsonb,
  command_desc = 'Full UAP overview'
where key = 'full-uap';

-- ------------------------------------------------------------
-- Check the result
-- ------------------------------------------------------------
select key, title, color,
       jsonb_array_length(fields) as fields,
       jsonb_array_length(links)  as buttons,
       length(description)        as desc_len
from public.entries
where key in ('work','sleep','wake-up','be-admin','full-uap')
order by key;
