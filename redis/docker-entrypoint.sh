#!/usr/bin/env bash
set -u

function dns-lookup
{
    # DNS lookup of the service
    for ip in $(getent hosts "${REDIS_DNS_LOOKUP_NAME}" | awk '{ print $1 }')
    do
        # Make sure the host is reachable
        if [ "$(redis-cli -h "$ip" -p "$REDIS_PORT" ${REDIS_PASSWORD:+-a "$REDIS_PASSWORD"} ping)" == 'PONG' ]
        then
            echo "$ip"
        fi
    done
}

function replicas
{
    echo "Waiting for ${REDIS_DNS_LOOKUP_EXPECT} replicas..." >&2
    while [ $(dns-lookup | wc -l) -lt ${REDIS_DNS_LOOKUP_EXPECT} ]
    do
        sleep 1s
    done

    # Return a subset of IP addresses
    dns-lookup | sort -u | head -${REDIS_DNS_LOOKUP_EXPECT}
}

function create-cluster
{
    sleep ${REDIS_DNS_LOOKUP_WAIT}
    local REDIS_HOSTS=$(replicas | sed "s/$/:$REDIS_PORT/g" | tr '\n' ' ' | sed 's: $::g')
    echo "Creating a cluster from $REDIS_HOSTS with $REDIS_CLUSTER_REPLICAS replicas..."
    redis-trib create --replicas ${REDIS_CLUSTER_REPLICAS} ${REDIS_HOSTS} <<< yes
}

: ${REDIS_CLUSTER_REPLICAS='1'}
: ${REDIS_DNS_LOOKUP_EXPECT='6'}
: ${REDIS_DNS_LOOKUP_NAME='redis'}
: ${REDIS_DNS_LOOKUP_WAIT='3s'}
: ${REDIS_PORT='6379'}

redis_exporter -redis.alias ${REDIS_ALIAS} &
create-cluster &
exec redis-server /etc/redis/redis.conf
