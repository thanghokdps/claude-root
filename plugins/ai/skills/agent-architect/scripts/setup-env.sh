#!/usr/bin/env bash
# setup-env.sh — creates the project's .env from .env.example, after the user's yes.
# Generates INTERNAL_API_TOKEN when the template leaves it empty, and never prints a value.
# Never overwrites an existing .env: its keys are the user's. Provider keys stay empty; the user adds them.
#   bash setup-env.sh [project-dir]
set -euo pipefail
dir="${1:-.}"
template="$dir/.env.example"
target="$dir/.env"

if [ ! -f "$template" ]; then
  echo "no .env.example in $dir: nothing created"
  exit 0
fi
if [ -e "$target" ]; then
  echo ".env already exists: left unchanged"
else
  token="$(openssl rand -base64 48)"
  umask 077
  awk -v token="$token" '/^INTERNAL_API_TOKEN=(\"\")?[[:space:]]*$/ { print "INTERNAL_API_TOKEN=\"" token "\""; next } { print }' "$template" > "$target"
  echo ".env created from .env.example"
fi

# Names only: a NAME= line with no value, or an empty pair of quotes.
empty="$(sed -nE "s/^([A-Z][A-Z0-9_]*)=(\"\"|'')?[[:space:]]*(#.*)?$/\1/p" "$target")"
if [ -n "$empty" ]; then
  echo "still empty:"
  printf '  %s\n' $empty
else
  echo "still empty: none"
fi
