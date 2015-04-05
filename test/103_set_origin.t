#!/bin/sh

test_description="Testing set_origin"

. ./setup.sh

test_expect_failure "Testing set_origin" "false"
test_expect_failure "Testing set_origin with --parent" "false"
test_done

# vim: set syntax=sh:
