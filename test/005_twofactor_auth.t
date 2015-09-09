#!/bin/sh

test_description="Testing two-factor authentication"

. ./setup.sh

test_expect_failure hub "Testing two factor authentication" "false"

test_done

# vim: set syntax=sh:
