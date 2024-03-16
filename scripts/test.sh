#! /usr/bin/env zsh

set -e

run_tests() {
  cd tests
  (python3 -m grader) || (
    python3 -V && return 1
  )
  cd ..
}

run_tests
