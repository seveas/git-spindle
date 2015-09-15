#!/bin/sh

test_description="Testing applying a branch"

. ./setup.sh

test_expect_failure "Applying a pull request" "false"
test_expect_failure "Applying a closed request" "false"
test_expect_failure "Applying a pull request to a different branch" "false"
test_done

# vim: set syntax=sh:
