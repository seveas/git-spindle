#!/bin/sh

test_description="Testing ignore"

. ./setup.sh

test_expect_success hub "Ignoring python files" "
    git_hub_1 ignore Python >actual &&
    grep docs/_build actual
"
test_expect_failure hub "Don't be case-sensitive" "
    git_hub_1 ignore python >actual &&
    grep docs/_build actual
"

test_done

# vim: set syntax=sh:
