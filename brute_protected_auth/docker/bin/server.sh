#!/usr/bin/env bash

set -e

gunicorn --workers=$WORKERS brute_protected_auth.wsgi:application --bind=0.0.0.0:80