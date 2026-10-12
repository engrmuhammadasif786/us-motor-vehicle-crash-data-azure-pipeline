{{ config(materialized='table') }}

with dedup as (
    select distinct state_name
    from {{ ref('stg_fars_accidents') }}
    where state_name is not null
),

states as (
    select
        state_name,
        row_number() over (order by state_name) as state_sk
    from dedup
)

select
    state_sk,
    state_name,
    current_timestamp as loaded_at
from states
