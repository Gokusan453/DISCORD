-- ============================================================
--  Content for /work  —  "system boot" style readout
--  Run in Supabase -> SQL Editor -> Run
--  Takes effect immediately, no redeploy needed.
-- ============================================================

update public.entries set
  title = '⚙️  WORK MODE',
  color = '57F287',
  description = E'```ansi\n'
    || E'[2;37mBooting workspace...[0m\n\n'
    || E'[2;32m▸[0m Starting system            [2;32m✓ done[0m\n'
    || E'[2;32m▸[0m Loading modules            [2;32m✓ done[0m\n'
    || E'[2;32m▸[0m Connecting to dev.giso.ai  [2;32m✓ online[0m\n'
    || E'[2;32m▸[0m Running analysis           [2;32m✓ complete[0m\n'
    || E'[2;32m▸[0m Sending report to phone    [2;32m✓ sent[0m\n'
    || E'```\n'
    || E'**All systems ready.** Everything is up and running. 🚀',
  url = 'https://dev.giso.ai',
  image_url = null,
  links = '[{"label": "Open dev.giso.ai", "url": "https://dev.giso.ai"}]'::jsonb,
  fields = E'[
      {"name": "Status",   "value": "🟢 Online",    "inline": true},
      {"name": "Analysis", "value": "✅ Complete",  "inline": true},
      {"name": "Phone",    "value": "📲 Notified",  "inline": true}
    ]'::jsonb,
  command_desc = 'Start the workspace'
where key = 'work';

-- Check the result
select key, title, url, jsonb_array_length(fields) as fields, jsonb_array_length(links) as buttons
from public.entries where key = 'work';
