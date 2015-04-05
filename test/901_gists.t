#!/bin/sh

test_description="Testing gists"

. ./setup.sh

test_expect_failure "Creating a gist from a file" "false"
test_expect_failure "Creating a gist from stdin" "false"
test_expect_failure "Listing gists" "false"
test_expect_failure "Cloning a gist" "false"
test_done

# vim: set syntax=sh:
