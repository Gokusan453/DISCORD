-- ============================================================
--  /analyze  —  "scanning messages" readout
--  Run in Supabase -> SQL Editor -> Run
--  Then run 2_register_commands.ps1 (it's a NEW command name)
-- ============================================================

insert into public.entries (key, title, dedicated, command_desc, color)
values ('analyze', '🛰️  MESSAGE ANALYSIS', true, 'Analyze new messages', '1ABC9C')
on conflict (key) do update set dedicated = true;

update public.entries set
  title = '🛰️  MESSAGE ANALYSIS',
  color = '1ABC9C',
  url   = 'https://dev.giso.ai',
  description =
       E'```ansi\n'
    || E'[1;37mScanning new messages[0m\n\n'
    || E'[1;36m▸[0m Reading new messages       [1;36mdone[0m\n'
    || E'[1;36m▸[0m Filtering noise            [1;36mdone[0m\n'
    || E'[1;36m▸[0m Analyzing content          [1;36mdone[0m\n'
    || E'[1;36m▸[0m Writing summary            [1;36mready[0m\n'
    || E'[1;36m▸[0m Sending to your phone      [1;36msent[0m\n\n'
    || E'[1;36m[██████████][0m [1;37m100%[0m\n'
    || E'```\n'
    || E'**Summary sent to your phone.** 📲  Check your notifications.',
  links  = '[{"label": "Open dev.giso.ai", "url": "https://dev.giso.ai"}]'::jsonb,
  fields = E'[
      {"name": "Messages", "value": "📥 Scanned",   "inline": true},
      {"name": "Summary",  "value": "📝 Ready",     "inline": true},
      {"name": "Phone",    "value": "📲 Sent",      "inline": true}
    ]'::jsonb,
  command_desc = 'Analyze new messages'
where key = 'analyze';

select key, title, color, jsonb_array_length(fields) as fields, jsonb_array_length(links) as buttons
from public.entries where key = 'analyze';
