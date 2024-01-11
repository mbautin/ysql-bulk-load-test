\timing on
drop table if exists test_table;
create extension if not exists pgcrypto;
create table test_table(k text, v text, PRIMARY KEY(k ASC));
create index index_v_test_table on test_table(v);

do $$
begin
  for counter in 1..NUM_GROUPS loop
    SELECT CURRENT_TIMESTAMP AS current_datetime;
    raise notice '[%s] counter: %', (current_datetime, counter * 10000);
    insert into test_table (select gen_random_uuid(), gen_random_bytes(50)::text
                        from generate_series(1, 10000) i);
    commit;
  end loop;
end $$;
