#!/bin/sh

test_description="Testing ls"

. ./setup.sh

test_expect_success "Cloning source repo" "
    git_hub_1 clone whelk
"

for spindle in lab hub bb; do
    test_expect_success "Testing ls ($spindle)" "
        git_${spindle}_1 ls whelk:master:/ | grep docs
    "

    test_expect_success "Testing ls for a non-default branch ($spindle)" "
        git_${spindle}_1 ls whelk:debian:debian | grep rules
    "

    test_expect_success "Testing ls inside repo ($spindle)" "
        (cd whelk &&
        git_${spindle}_1 ls / | grep docs &&
        git_${spindle}_1 ls | grep docs &&
        git_${spindle}_1 ls debian:debian | grep rules)
    "

    test_expect_success "Testing ls without specifying a branch ($spindle)" "
        git_${spindle}_1 ls whelk:: | grep docs &&
        git_${spindle}_1 ls whelk::docs | grep presentation
    "

    test_expect_failure "Testing ls against a relative path ($spindle)" "
        (cd whelk/docs &&
        git_${spindle}_1 ls | grep presentation)
    "
done

test_done

# vim: set syntax=sh:
