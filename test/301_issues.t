#!/bin/sh

test_description="Testing issues"

. ./setup.sh

test_expect_failure "Filing an issue" "false"
test_expect_failure "Listing issues" "false"
test_done

# vim: set syntax=sh:
