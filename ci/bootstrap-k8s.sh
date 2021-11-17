#! /bin/bash
set -euo pipefail
shopt -s expand_aliases

source ci/bootstrap/src/k8s/bootstrap.sh

export PATH="$PATH:$PWD/ci/bootstrap/bin:$PWD/bin"

function deploy-argo {
    export ARGOCD_APP_URL=https://${COMPONENT_NAME}-${CI_COMMIT_REF_SLUG}.${KUBE_NAMESPACE}.${ARGOCD_BASE_DOMAIN}
    # Create the ArgoCD review app if it does not exist yet or update it (see the '--upsert' switch)
    
    function create
    {
        set - \
            --auto-prune \
            --dest-namespace $KUBE_NAMESPACE \
            --dest-server https://kubernetes.default.svc \
            --path $ARGOAPP_REPO_PATH \
            --project $ARGOCD_PROJECT \
            --repo $ARGOCD_KUBE_REPO_URL_HTTPS \
            --revision $ARGOAPP_REPO_BRANCH \
            --sync-option Validate=false \
            --sync-policy automated \
            --sync-retry-backoff-duration 5s \
            --sync-retry-backoff-factor 2 \
            --sync-retry-backoff-max-duration 3m \
            --sync-retry-limit 5 \
            --auth-token $ARGOCD_AUTH_TOKEN \
            --server $ARGOCD_SERVER \
            --upsert \
            --values $HELM_VALUES \
            --grpc-web

        if [ "$PRODUCTION" = false ]; then
          echo "is Development so override"
          export IMAGE_NAME=${CI_REGISTRY_IMAGE}/${COMPONENT_NAME}@${IDUNN_DEV_IMAGE_DIGEST}
          echo "deploy using image: $IMAGE_NAME"
          set - $@ --helm-set-string $ARGOCD_SUBCHART_NAME.global.registry.url="$CI_REGISTRY" \
                 --helm-set-string $ARGOCD_SUBCHART_NAME.global.registry.username="$CI_DEPLOY_USER" \
                 --helm-set-string $ARGOCD_SUBCHART_NAME.global.registry.password="$CI_DEPLOY_PASSWORD" \
                 --helm-set-string $ARGOCD_SUBCHART_NAME.fullnameOverride="$FULLNAME_OVERRIDE" \
                 --helm-set-string $ARGOCD_SUBCHART_NAME.image.name="$IMAGE_NAME"
        fi

        argocd app create $ARGOCD_APP_NAME $ARGOCD_OPTS $@
    }
    
    
    create
    
    argocd app wait $ARGOCD_APP_NAME $ARGOCD_OPTS \
      --health \
      --timeout $ARGOCD_TIMEOUT \
      --auth-token $ARGOCD_AUTH_TOKEN \
      --server $ARGOCD_SERVER \
      --grpc-web

    DEPLOY_PIPELINE="\#[$CI_PIPELINE_ID]($CI_PIPELINE_URL)"
    DEPLOY_REF="[$CI_COMMIT_REF_NAME]($CI_PROJECT_URL/-/tree/$CI_COMMIT_REF_NAME)"
    DEPLOY_USER="@${GITLAB_USER_NAME}"

    /usr/local/bin/go-mattermost-notify post \
          --author  "Dev Tools" \
          --channel "$DEPLOY_USER" \
          --level   "success" \
          --message "Pipeline $DEPLOY_PIPELINE triggered by $DEPLOY_USER successfully deployed $DEPLOY_REF to **$ARGOCD_APP_URL**" \
          --title   "Execution Status for $FULLNAME_OVERRIDE" \
          --quiet || true
}
