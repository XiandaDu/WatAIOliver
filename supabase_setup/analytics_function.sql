-- Analytics RPC: compute course-level message analytics on the DB side
create or replace function public.get_course_analytics_counts(p_course_id text)
returns jsonb
language plpgsql
stable
as $$
declare
  result jsonb;
begin
  with days as (
    select (current_date - i) as d
    from generate_series(6, 0, -1) as i
  ),
  day_counts as (
    select d,
           coalesce((
             select count(*)
             from public.messages m
             where m.course_id = p_course_id
               and m.created_at::date = d
           ), 0) as cnt
    from days
  ),
  totals as (
    select
      (select count(distinct m.conversation_id) from public.messages m where m.course_id = p_course_id) as total_conversations,
      (select count(distinct m.user_id) from public.messages m where m.course_id = p_course_id and m.user_id is not null) as active_users
  ),
  models as (
    select coalesce(model, 'unknown') as model_key, count(*)::int as model_count
    from public.messages
    where course_id = p_course_id and sender = 'assistant'
    group by coalesce(model, 'unknown')
  ),
  day_labels as (
    select jsonb_agg(to_char(d, 'Dy') order by d) as labels
    from day_counts
  ),
  day_counts_agg as (
    select jsonb_agg(cnt order by d) as counts
    from day_counts
  )
  select jsonb_build_object(
    'total_conversations', totals.total_conversations,
    'active_users', totals.active_users,
    'usage_by_day', jsonb_build_object(
      'labels', day_labels.labels,
      'counts', day_counts_agg.counts
    ),
    'conversations_by_model', coalesce((select jsonb_object_agg(model_key, model_count) from models), '{}'::jsonb)
  ) into result
  from totals, day_labels, day_counts_agg;

  return result;
end;
$$;

-- Grant execute permission
grant execute on function public.get_course_analytics_counts(text) to authenticated;
grant execute on function public.get_course_analytics_counts(text) to service_role;
