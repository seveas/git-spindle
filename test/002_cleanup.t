#!/bin/sh

test_description="Deletes repos and keys for the test users"

. ./setup.sh

export DEBUG=1

for spindle in hub lab bb; do for account in 1 2 3; do
    test_expect_success "Clean up git${spindle} account ${account} (cleanup)" "
        git_${spindle}_${account} test-cleanup
    "
done; done
for spindle in hub lab bb; do for account in 1 2 3; do
    test_expect_success "Clean up git${spindle} account ${account} (verify)" "
        : > expected &&
        git_${spindle}_${account} repos > actual &&
        git_${spindle}_${account} public-keys >> actual &&
        test_cmp expected actual
    "
done; done

test_done

# vim: set syntax=sh:
