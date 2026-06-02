create table if not exists public.prediction_logs (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  filename text,
  content_type text,
  predicted_class text not null,
  probability numeric(8, 6) not null,
  infection_ratio numeric(8, 6) not null,
  severity text not null,
  processing_time_ms integer not null
);

alter table public.prediction_logs enable row level security;

revoke all on table public.prediction_logs from anon, authenticated;

comment on table public.prediction_logs is
  'Server-side prediction telemetry for cassava leaf analyses. Inserts should use a Supabase service role key only.';
