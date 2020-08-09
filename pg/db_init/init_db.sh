#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE TABLE geo (
        country_code char(2),
        zipcode      varchar(20),
        city         varchar(180),
        state        varchar(100),
        state_code   varchar(20),
        admin_name2  varchar(100),
        admin_code2  varchar(20),
        admin_name3  varchar(100),
        admin_code3  varchar(20),
        latitude     real,
        longitude    real,
        accuracy     smallint
    );
    CREATE INDEX city_state_code on geo (UPPER(city || state_code));
    CREATE INDEX city_state on geo (UPPER(city || state));
    COPY geo FROM '/app/data/US.txt' WITH (FORMAT CSV, DELIMITER E'\t', FORCE_NULL(accuracy));
    VACUUM ANALYZE geo;
EOSQL
ogr2ogr -f "PostgreSQL" PG:"dbname=postgres  user=postgres" "data/indigenousTerritories.json"