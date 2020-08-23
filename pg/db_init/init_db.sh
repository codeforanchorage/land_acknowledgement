#!/bin/bash
set -e

ogr2ogr -f "PostgreSQL" PG:"dbname=postgres  user=postgres" "data/indigenousTerritories.json"