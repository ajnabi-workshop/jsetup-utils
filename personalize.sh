#!/usr/bin/env bash

set -e

indent() {
    sed 's/^/    /'
}

if [ -z "$1" ]; then
  echo "Usage: personalize <template_name>"
  exit 1
fi

TEMPLATE_NAME="$1"
PROJ_NAME="$(basename "$(pwd)")"

if [ "$PKG_NAME_DEF" = "$REPO_NAME" ]; then
  exit 0
fi

read -p "Personalize repository? [Y/n] " input
input=${input:-Y}
if [[ $input =~ ^[Yy]$ ]]; then
  personalize=true
else
  personalize=false
fi
if $personalize; then
  AUTH_NAME_DEF=$(git config --default "Firstname Lastname" --get user.name)
  read -r -p "Project Author [$AUTH_NAME_DEF]: " AUTHNAME
  AUTH_NAME=${AUTH_NAME:-$AUTH_NAME_DEF}

  EMAIL_DEF=$(git config --default "user@email.com" --get user.email)
  read -r -p "Maintainer Email [$EMAIL_DEF]: " EMAIL
  EMAIL=${EMAIL:-$EMAIL_DEF}

  echo "Preparing ${PKG_NAME}.cabal..."
  (
    set -x
    git ls-files | grep -v '\.justfile$' | xargs -I _ sed -i \
        -e "s#$TEMPLATE_NAME#$PROJ_NAME#g" _ \
        -e "s#Ian Burzynski#$AUTH_NAME#g" _ \
        -e "s#23251244+iburzynski@users.noreply.github.com#$EMAIL#g _"
    mv "$TEMPLATE_NAME.cabal" "$PROJ_NAME.cabal"
  ) 2>&1 | indent

  read -p "Replace README? [Y/n] " input
  input=${input:-Y}
  if [[ $input =~ ^[Yy]$ ]]; then
    replace_readme=true
  else
    replace_readme=false
  fi
  if $replace_readme; then
    echo "Creating README..."
    (
    set -x
    mv "README.md" "docs/README.md"
    cp "README_TEMPLATE.md" "README.md"
    ) 2>&1 | indent
  fi
fi