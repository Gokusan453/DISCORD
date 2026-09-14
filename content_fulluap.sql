-- ============================================================
--  Update /full-uap  —  local server + G's assistant BELLA
--  Run in Supabase -> SQL Editor -> Run  (no redeploy needed)
-- ============================================================

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
    || E'[1;35m▸[0m Uploading to local server  [1;35mdone[0m\n'
    || E'[1;35m▸[0m Sending to G''s assistant   [1;35mBELLA[0m\n\n'
    || E'[1;35m[██████████][0m [1;37m100%[0m\n'
    || E'```\n'
    || E'**Full UAP overview is ready.** 📊  Sent to BELLA.',
  links  = '[{"label": "View full report", "url": "https://dev.giso.ai"}]'::jsonb,
  fields = E'[
      {"name": "Report",   "value": "📋 Complete",  "inline": true},
      {"name": "Server",   "value": "🖥️ Local",     "inline": true},
      {"name": "Sent to",  "value": "🤖 BELLA",     "inline": true}
    ]'::jsonb,
  command_desc = 'Full UAP overview'
where key = 'full-uap';

select key, title, length(description) as desc_len,
       jsonb_array_length(fields) as fields, jsonb_array_length(links) as buttons
from public.entries where key = 'full-uap';
