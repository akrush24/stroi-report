#!/bin/bash
set -ex

mkdir -p db_backups
sqlite3 instance/mydatabase.db '.dump' > db_backups/$(date +%Y%M%d%H%M).sql
