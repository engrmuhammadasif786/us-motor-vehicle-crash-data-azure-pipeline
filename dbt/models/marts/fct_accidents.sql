{{ config(
    materialized='table',
    partition_by={
        "field": "crash_year",
        "data_type": "int",
        "range": {
            "start": 2010,
            "end": 2026,
            "interval": 1
        }
    } if target.type == 'snowflake' else None,
    cluster_by=["state_name"] if target.type == 'snowflake' else None
) }}

with accidents as (
    select * from {{ ref('stg_fars_accidents') }}
),

state_dim as (
    select * from {{ ref('dim_state') }}
),

final as (
    select
        a.case_number,
        a.crash_date,
        extract(year from a.crash_date) as crash_year,
        extract(month from a.crash_date) as crash_month,
        a.crash_hour,
        a.crash_minute,
        a.state_name,
        s.state_sk,
        a.county_name,
        a.city_name,
        cast(a.fatalities as integer) as fatalities,
        cast(a.drunk_drivers as integer) as drunk_drivers,
        a.total_vehicles,
        a.pedestrians,
        a.light_condition,
        a.weather_condition,
        a.harmful_event,
        a.manner_of_collision,
        a.relation_to_junction,
        a.relation_to_roadway,
        a.type_of_intersection,
        a.trafficway_flow,
        a.traffic_control_device,
        a.school_bus_related,
        a.route,
        a.functional_system_name,
        a.road_owner_name,
        a.speed_limit,
        a.loaded_at
    from accidents a
    left join state_dim s on a.state_name = s.state_name
)

select * from final
