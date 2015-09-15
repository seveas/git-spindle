#!/bin/sh

test_description="Testing say"

. ./setup.sh

test_expect_success hub "Testing say" "
    git_hub_1 say 'Hello, world' >actual &&
    grep 'Hello, world' actual
"
test_done

# vim: set syntax=sh:
