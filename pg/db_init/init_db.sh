#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE TABLE geo (
        state_code   char(2),
        state        varchar(100),
        city         varchar(180),
        latitude     real,
        longitude    real
    );
    CREATE TABLE zipcode (
        zipcode      char(5),
        state        varchar(100),
        city         varchar(180),
        latitude     real,
        longitude    real
    );
    CREATE INDEX concat_city_state ON geo (regexp_replace(UPPER(city || state), '\W+', '', 'g'));
    CREATE INDEX concat_city_state_code ON geo (regexp_replace(UPPER(city || state_code), '\W+', '', 'g'));
    CREATE INDEX zips on zipcode (zipcode);
    COPY geo FROM '/app/data/2019_GNIS_POP_PLACES.txt' WITH (FORMAT CSV, DELIMITER E'|');
    COPY zipcode FROM '/app/data/zipcodes.txt' WITH (FORMAT CSV, DELIMITER E'|');

    VACUUM ANALYZE geo;
    VACUUM ANALYZE zipcode;

EOSQL
ogr2ogr -f "PostgreSQL" PG:"dbname=postgres  user=postgres" "data/indigenousTerritories.json"