#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE TABLE geo (
        state_code   char(2),
        state        varchar(100),
        city         varchar(180),
        latitude     real,
        longitude    real,
    );
    CREATE INDEX city_state_code on geo (UPPER(city || state_code));
    CREATE INDEX city_state on geo (UPPER(city || state));
    COPY geo FROM '/app/data/2019_GNIS_POP_PLACES.txt' WITH (FORMAT CSV, DELIMITER E'|', FORCE_NULL(accuracy));
EOSQL
ogr2ogr -f "PostgreSQL" PG:"dbname=postgres  user=postgres" "data/indigenousTerritories.json"