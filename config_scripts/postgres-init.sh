#!/usr/bin/env bash

PGPASSWORD=${PGPASSWORD} psql --username=${PGUSER} --host=${PGHOST} -v ON_ERROR_STOP=1 <<-EOSQL
CREATE DATABASE kong;
GRANT ALL PRIVILEGES ON DATABASE kong TO postgres;
EOSQL
