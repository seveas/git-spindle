#!/bin/sh

test_description="Testing mirror"

. ./setup.sh

test_expect_failure "Testing mirror" "false"
test_expect_failure "Testing mirror --goblet" "false"
test_done

# vim: set syntax=sh:
