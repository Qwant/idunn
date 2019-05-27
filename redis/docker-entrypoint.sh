#!/usr/bin/env bash
set -euo pipefail

redis-server --version
redis_exporter &
exec envsubst < '/usr/local/etc/redis/redis.conf' | redis-server -
