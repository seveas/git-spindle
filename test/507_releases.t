#!/bin/sh

test_description="Testing releases"

. ./setup.sh

test_expect_failure hub "Testing releases" "
    false
"

test_done

# vim: set syntax=sh:
