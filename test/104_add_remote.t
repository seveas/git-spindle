#!/bin/sh

test_description="Testing add_remote"

. ./setup.sh

test_expect_failure "Testing add_remote" "false"
test_expect_failure "Testing add_remote on different spindle (add BB remote on GH repo)" "false"
test_done

# vim: set syntax=sh:
