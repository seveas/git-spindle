#!/bin/sh

test_description="Deletes repos and keys for the test users"

. ./setup.sh

export DEBUG=1

for spindle in $all_spindles; do
    test_expect_success "Clean up $spindle (cleanup)" "
        $spindle test-cleanup
    "
done
for spindle in $all_spindles; do
    test_expect_success "Clean up $spindle (verify)" "
        : > expected &&
        $spindle repos > actual &&
        $spindle public-keys >> actual &&
        test_cmp expected actual
    "
done

test_done

# vim: set syntax=sh:
