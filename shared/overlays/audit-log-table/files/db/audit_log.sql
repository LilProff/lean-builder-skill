-- Audit log: who did what, to which record, and what changed. Append-only.
-- Run in the Supabase SQL editor (or as a migration). Write to it from the server, never from the browser.

create table if not exists audit_log (
  id uuid primary key default gen_random_uuid(),
  actor_id uuid,
  action text not null,          -- e.g. 'trip.update', 'invoice.approve'
  entity text not null,          -- e.g. 'trips'
  entity_id text,
  before jsonb,
  after jsonb,
  created_at timestamptz not null default now()
);

create index if not exists audit_log_entity_idx on audit_log (entity, entity_id);
create index if not exists audit_log_actor_idx on audit_log (actor_id, created_at desc);

alter table audit_log enable row level security;

-- No insert policy on purpose: only your server writes rows, using the service role key, which bypasses
-- row level security. Browsers cannot add, edit or remove entries.

-- Only admins may read the log. Uses org_members from db/rls_template.sql (overlay rls-policies).
create policy audit_log_select on audit_log
  for select to authenticated
  using (exists (select 1 from org_members m where m.user_id = (select auth.uid()) and m.role = 'admin'));

-- No update or delete policy on purpose: the log cannot be edited or removed by users.
