#!/bin/sh

test_description="Testing calendar"

. ./setup.sh

test_expect_failure "Testing GitHub calendar" "false"
test_expect_failure "Testing GitLab calendar" "false"
test_done

# vim: set syntax=sh:
