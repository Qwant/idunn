#! /bin/bash
set -euo pipefail
shopt -s expand_aliases

source ci/bootstrap/src/bootstrap.sh

export PATH="$PWD/ci/bootstrap/bin:$PATH"

function deploy
{
    local STACK_FILE='docker-stack.yml'

    guess ENVIRONMENT from CI_JOB_NAME
    guess APP_HOST from CI_ENVIRONMENT_URL

    docker-service-network config "${STACK_NAME}_idunn" | tee docker-networks.yml
    COMPOSE_FILE="$COMPOSE_FILE:docker-networks.yml"

    mv docker-content-digest.env .env

    docker-compose config | tee "$STACK_FILE"
    docker stack deploy --compose-file "$STACK_FILE" --with-registry-auth "$STACK_NAME"
    docker service update --network-add "${STACK_NAME}_default" "$ROUTER_SERVICE_NAME" || true
    docker service update --network-add "${STACK_NAME}_default" "$PROMETHEUS_SERVICE_NAME" || true
    docker service update --network-add "${STACK_NAME}_default" "$NLU_SERVICE_NAME" || true
    docker-stack-deploy-wait -t 600 "$STACK_NAME"
}
