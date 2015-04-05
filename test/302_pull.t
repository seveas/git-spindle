#!/bin/sh

test_description="Testing pull requests"

. ./setup.sh

test_expect_failure "Filing a pull request" "false"
test_expect_failure "Filing a pull request against a different branch" "false"
test_expect_failure "Filing a pull request for an unpushed branch" "false"
test_expect_failure "Turning an issue into a pull request" "false"
test_expect_failure "Listing pull requests" "false"
test_done

# vim: set syntax=sh:
