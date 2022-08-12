#! /bin/bash
set -euo pipefail
shopt -s expand_aliases
 
source ci/bootstrap/src/bootstrap.sh
export PATH="$PATH:$PWD/ci/bootstrap/bin"
