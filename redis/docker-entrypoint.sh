#!/usr/bin/env bash
set -u

redis-server --version
redis_exporter &
exec envsubst < '/usr/local/etc/redis/redis.conf' | redis-server -
