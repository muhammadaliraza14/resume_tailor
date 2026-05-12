#!/bin/sh
set -e
umask 022
mkdir -p /app/output/web_jobs
if [ "$(id -u)" = "0" ]; then
  chown -R app:app /app/output
  exec gosu app /docker/cmd.sh
fi
exec /docker/cmd.sh
