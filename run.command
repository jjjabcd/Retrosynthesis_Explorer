#!/usr/bin/env bash
cd -- "$(dirname -- "$0")" || exit 1
./run.sh "$@"
status=$?
if [[ $status -ne 0 ]]; then read -r -p 'Startup failed. Press Return to close.'; fi
exit "$status"
