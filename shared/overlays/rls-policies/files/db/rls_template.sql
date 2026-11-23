-- Row level security template: every row belongs to an organisation (org_id),
-- and a user sees only the rows of organisations they are a member of.
-- Run in the Supabase SQL editor. Copy the policy block for each table that holds client data.

create table if not exists org_members (
  org_id uuid not null,
  user_id uuid not null,
  role text not null default 'member',
  primary key (org_id, user_id)
);

alter table org_members enable row level security;

create policy org_members_select on org_members
  for select to authenticated
  using (user_id = auth.uid());

-- Example table. Replace "records" and its columns with your own.
create table if not exists records (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null,
  title text not null,
  created_by uuid default auth.uid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists records_org_idx on records (org_id);

alter table records enable row level security;

create policy records_select on records
  for select to authenticated
  using (org_id in (select org_id from org_members where user_id = auth.uid()));

create policy records_insert on records
  for insert to authenticated
  with check (org_id in (select org_id from org_members where user_id = auth.uid()));

create policy records_update on records
  for update to authenticated
  using (org_id in (select org_id from org_members where user_id = auth.uid()))
  with check (org_id in (select org_id from org_members where user_id = auth.uid()));

-- Only organisation admins may delete.
create policy records_delete on records
  for delete to authenticated
  using (org_id in (select org_id from org_members where user_id = auth.uid() and role = 'admin'));
