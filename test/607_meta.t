#!/bin/sh

test_description="GitHub's meta functionality"

. ./setup.sh

test_expect_success hub "Testing ip-addresses" "
    git_hub_1 ip-addresses --pages > actual &&
    test \$(wc -l <actual) -gt 0 &&
    git_hub_1 ip-addresses --hooks > actual &&
    test \$(wc -l <actual) -gt 0 &&
    git_hub_1 ip-addresses --git > actual &&
    test \$(wc -l <actual) -gt 0 &&
    git_hub_1 ip-addresses --importer > actual &&
    test \$(wc -l <actual) -gt 0
"

test_done

# vim: set syntax=sh:
