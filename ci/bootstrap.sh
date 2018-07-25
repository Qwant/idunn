#! /bin/bash
set -euo pipefail
shopt -s expand_aliases
export PATH="$PWD/bin:$PWD/ci:$PATH"
export UID
export GID

# avoid undefined variables in Makefiles
alias make="make --warn-undefined-variables --no-keep-going"

# source src/bootstrap.sh from GitLab
source <(curl --silent --show-error "https://git.qwant.ninja/continuous-integration/gitlab-runner-bootstrap/raw/master/src/bootstrap.sh")

export NO_PROXY="10.103.9.1,$NO_PROXY"
export no_proxy="10.103.9.1,$no_proxy"
