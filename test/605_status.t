#!/bin/sh

test_description="Testing GitHub status"

. ./setup.sh

test_expect_success hub "Testing git hub status" "
    git_hub_1 status > actual &&
    grep -v '^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] \\(good\\|minor\\|major\\)' actual &&
    tail -n1 actual | grep -q 'Current status'
"
test_done

# vim: set syntax=sh:
