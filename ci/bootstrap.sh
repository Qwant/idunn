#! /bin/bash
set -euo pipefail
shopt -s expand_aliases
export PATH="$PWD/ci/bin:$PWD/bin:$PATH"

# avoid undefined variables in Makefiles
alias make="make --warn-undefined-variables --no-keep-going"

# source src/bootstrap.sh from GitLab
source <(curl --silent --show-error "https://git.qwant.ninja/continuous-integration/gitlab-runner-bootstrap/raw/87c2437224964ce7f40680dff37471a329d46d76/src/bootstrap.sh")

# Guess some variables
function guess # <variable name> from <variable name>
{
    function process # <value>
    {
        if [[ $? == 0 ]]
        then
            echo "Guessing ${FUNCNAME[1]}: $1" >&2
            export ${FUNCNAME[1]}="$1"
        fi
    }

    function APP_HOST # from CI_ENVIRONMENT_URL
    {
        process $(sed -E 's|^(http[s]?://)?([^/]+).*$|\2|g' <<< "${!2}")
    }

    function ENVIRONMENT # from CI_JOB_NAME
    {
        process $(grep -Po '(review|development|prelive|production)' <<< "${!2}")
    }

    "$@"
}

function url
{
    function host
    {
        sed -E 's|^(tcp://)?([^/:]+).*(:\d+)?$|\2|g' <<< "$1"
    }

    "$@"
}

function deploy
{
    local STACK_FILE='docker-stack.yml'

    export DOCKER_IMAGE_DIGEST="$(cat idunn.digest)"
    export REDIS_IMAGE_DIGEST=$(docker-content-digest-qwant \
        "${CI_PROJECT_PATH}/idunn-redis" "latest")

    guess ENVIRONMENT from CI_JOB_NAME
    guess APP_HOST from CI_ENVIRONMENT_URL

    docker-service-network config "${STACK_NAME}_idunn" > docker-networks.yml

    COMPOSE_FILE="$COMPOSE_FILE:docker-networks.yml"

    docker-compose config | tee "$STACK_FILE"
    docker stack deploy --compose-file "$STACK_FILE" --with-registry-auth "$STACK_NAME"
    docker service update --network-add "${STACK_NAME}_default" "$ROUTER_SERVICE_NAME" || true
    if [ ! -z ${KUZZLE_SERVICE_NAME+x} ]; then
        docker service update --network-add "${STACK_NAME}_default" "$KUZZLE_SERVICE_NAME" || true
    fi
    docker-stack-wait -t 600 "$STACK_NAME"
}

function stop
{
    docker service update --network-rm "${STACK_NAME}_default" "$ROUTER_SERVICE_NAME" || true
    if [ ! -z ${KUZZLE_SERVICE_NAME+x} ]; then
        docker service update --network-rm "${STACK_NAME}_default" "$KUZZLE_SERVICE_NAME" || true
    fi
    docker stack rm "$STACK_NAME"
}
