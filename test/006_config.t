#!/bin/sh

test_description="Testing git * config"

. ./setup.sh

test_expect_failure "Testing config setting" "false"
test_expect_failure "Testing config getting" "false"
test_expect_failure "Testing config unsetting" "false"

test_done

# vim: set syntax=sh:
