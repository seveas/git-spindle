#!/bin/sh

test_description="Testing docstring propagation"

. ./setup.sh

test_expect_failure "Is README up-to-date" "false"
test_expect_failure "Are usage strings in docs/ up-to-date" "false"

test_done

# vim: set syntax=sh:
