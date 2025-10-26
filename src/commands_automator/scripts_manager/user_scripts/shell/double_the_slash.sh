#!/bin/bash

path="$1"

if [[ -z "$path" ]]; then
  echo "Error: No path provided" >&2
  exit 1
fi

echo "$path" | perl -pe 's/\//\\\//g'