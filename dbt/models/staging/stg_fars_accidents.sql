with source as (
    select * from {{ source('fars_raw', 'raw_accidents') }}
),

renamed as (
    select
        cast(ST_CASE as integer) as case_number,
        cast(VE_TOTAL as integer) as total_vehicles,
        cast(VE_FORMS as integer) as vehicle_forms,
        cast(PEDS as integer) as pedestrians,
        cast(PERNOTMVIT as integer) as persons_not_in_motor_vehicle,
        cast(PERMVIT as integer) as persons_in_motor_vehicle,

        make_date(cast(YEAR as integer), cast(MONTH as integer), cast(DAY as integer)) as crash_date,
        cast(HOUR as integer) as crash_hour,
        cast(MINUTE as integer) as crash_minute,

        trim(STATENAME) as state_name,
        trim(COUNTYNAME) as county_name,
        trim(CITYNAME) as city_name,
        cast(FATALS as integer) as fatalities,
        cast(NULL as integer) as drunk_drivers,
        trim(LGT_CONDNAME) as light_condition,
        trim(WEATHERNAME) as weather_condition,
        trim(HARM_EVNAME) as harmful_event,
        trim(MAN_COLLNAME) as manner_of_collision,
        trim(RELJCT1NAME) as relation_to_junction,
        trim(REL_ROADNAME) as relation_to_roadway,
        trim(TYP_INTNAME) as type_of_intersection,
        cast(NULL as varchar) as trafficway_flow,
        cast(NULL as varchar) as traffic_control_device,
        trim(SCH_BUSNAME) as school_bus_related,
        cast(ROUTE as integer) as route,
        cast(FUNC_SYS as integer) as functional_system,
        trim(FUNC_SYSNAME) as functional_system_name,
        cast(RD_OWNER as integer) as road_owner,
        trim(RD_OWNERNAME) as road_owner_name,
        cast(NULL as integer) as speed_limit,
        current_timestamp as loaded_at

    from source
)

select * from renamed
