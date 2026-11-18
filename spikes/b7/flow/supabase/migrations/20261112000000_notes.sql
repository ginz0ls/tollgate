create table public.notes (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id),
  title text not null,
  body text not null default '',
  created_at timestamptz not null default now()
);

alter table public.notes enable row level security;

create policy "notes_select_own" on public.notes
  for select to authenticated
  using (auth.uid() = user_id);
