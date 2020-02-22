#!/usr/bin/env bash

set -e
echo "In entrypoint"
while ! nc -z database 5432; do
  sleep 3;
  echo "waiting database..."
done

while ! nc -z redis 6379; do
  sleep 3;
  echo "waiting redis..."
done

eval "/bin/makemigrations.sh"
eval "/bin/migrate.sh"
exec "$@"