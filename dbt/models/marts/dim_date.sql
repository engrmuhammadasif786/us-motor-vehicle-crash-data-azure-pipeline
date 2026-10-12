{{ config(materialized='table') }}

with date_spine as (
    select
        date '2010-01-01' + interval '1 day' * (row_number() over () - 1) as date_key
    from range(0, 5844)  -- 2010-01-01 to 2025-12-31
),

dim_date as (
    select
        date_key,
        extract(year from date_key) as year,
        extract(month from date_key) as month,
        extract(day from date_key) as day,
        extract(quarter from date_key) as quarter,
        extract(dow from date_key) as day_of_week,
        case
            when extract(dow from date_key) in (0, 6) then true
            else false
        end as is_weekend,
        strftime(date_key, '%B') as month_name,
        strftime(date_key, '%A') as day_name
    from date_spine
)

select * from dim_date
