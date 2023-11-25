#!/usr/bin/env bash

FORCE_MERGE=false
REPO_NAME=""

while getopts "f" opt; do
  case ${opt} in
    f ) FORCE_MERGE=true ;;
    \? ) echo "Usage: jupdate [-f] <repo_name>"; exit 1 ;;
  esac
done

shift $((OPTIND - 1))

if [ -z "$1" ]; then
  echo "Usage: jupdate [-f] <repo_name>"
  exit 1
fi

REPO_NAME=$1
GITHUB_URL="https://github.com/iburzynski/${REPO_NAME}"

if ! git remote | grep -q "^upstream$"; then
  git remote add upstream "$GITHUB_URL"
fi

git fetch upstream --recurse-submodules

if [ "$FORCE_MERGE" = true ]; then
  git checkout HEAD -- "*.cabal" "src/Contracts.hs"
fi

git merge upstream/main --allow-unrelated-histories

git submodule update --recursive