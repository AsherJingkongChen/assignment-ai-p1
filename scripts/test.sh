#! /usr/bin/env zsh

set -e

run_tests() {
  (cp src/submission.py tests/submission.py) || (
    echo "Usage: ./scripts/test.sh" && return 1
  )
  cd tests
  (python3 -m grader) || (
    python3 -V && return 1
  )
  cd ..
}

run_tests
