#!/usr/bin/env bash
# Usage: retry-once.sh <seconds> <command> [args...]
# Runs the command with a time limit per attempt and one retry, so a stalled install fails fast.
set -u
limit=$1
shift
for attempt in 1 2; do
  timeout --kill-after=10 "$limit" "$@" && exit 0
  echo "::warning::attempt $attempt of '$*' failed or timed out (limit ${limit}s)"
  # A killed install can leave apt-get alive for a moment, still holding the dpkg lock.
  # RETRY_PAUSE lets the tests skip the pause; unset (as in CI) it is 20 s
  [[ "$attempt" = 1 ]] && sleep "${RETRY_PAUSE:-20}"
done
exit 1
