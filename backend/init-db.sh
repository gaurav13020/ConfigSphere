#!/bin/bash
# Creates the authsphere database alongside configsphere.
# Runs automatically on first container start via docker-entrypoint-initdb.d/.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE authsphere'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'authsphere')\gexec
EOSQL
