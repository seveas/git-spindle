#!/bin/sh

test_description="Testing cat"

. ./setup.sh

test_expect_success "Cloning source repo" "
    git_hub_1 clone whelk &&
    cat whelk/setup.py | md5sum > expected.plain &&
    cat whelk/docs/presentation/whelk.jpg | md5sum > expected.binary &&
    git -C whelk checkout -b debian origin/debian -- &&
    cat whelk/debian/rules | md5sum > expected.branch &&
    git -C whelk remote rm origin
"

for spindle in lab hub bb; do
    test_expect_success "Testing cat ($spindle)" "
        git_${spindle}_1 cat whelk:master:setup.py | md5sum > actual &&
        test_cmp expected.plain actual
    "

    test_expect_success "Testing cat for a non-default branch ($spindle)" "
        git_${spindle}_1 cat whelk:debian:debian/rules | md5sum > actual &&
        test_cmp expected.branch actual
    "

    test_expect_success "Testing cat for binary files ($spindle)" "
        git_${spindle}_1 cat whelk:master:docs/presentation/whelk.jpg | md5sum > actual &&
        test_cmp expected.binary actual
    "

    test_expect_success "Testing cat inside repo ($spindle)" "
        (cd whelk &&
        git_${spindle}_1 cat setup.py | md5sum > actual &&
        test_cmp ../expected.plain actual
        git_${spindle}_1 cat debian:debian/rules | md5sum > actual &&
        test_cmp ../expected.branch actual)
    "

    test_expect_success "Testing cat without specifying a branch ($spindle)" "
        git_${spindle}_1 cat whelk::setup.py | md5sum > actual &&
        test_cmp expected.plain actual
    "

    test_expect_failure "Testing cat against a relative path ($spindle)" "false"
done

test_done

# vim: set syntax=sh:
