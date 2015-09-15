#!/bin/sh

test_description="Test the browse functionality"

. ./setup.sh

for spindle in hub lab bb; do
    test_expect_success $spindle "Launch browsers for repo homepage ($spindle)" "
        echo https://$(spindle_host git_${spindle}_1)/seveas/whelk > expected
        git_${spindle}_1 browse seveas/whelk > actual
        test_cmp expected actual
    "
    test_expect_success $spindle "Launch browsers for repo issues page ($spindle)" "
        echo https://$(spindle_host git_${spindle}_1)/seveas/whelk/issues > expected
        git_${spindle}_1 browse seveas/whelk issues > actual
        test_cmp expected actual
    "
    test_expect_success $spindle "Launch browser from within a repo ($spindle)" "
        rm -rf whelk &&
        git_${spindle}_1 clone seveas/whelk &&
        (cd whelk &&
        cat >expected <<EOF &&
https://$(spindle_host git_${spindle}_1)/seveas/whelk
https://$(spindle_host git_${spindle}_1)/seveas/whelk/issues
EOF
        git_${spindle}_1 browse >actual &&
        git_${spindle}_1 browse issues >>actual &&
        test_cmp expected actual)
    "
done

test_done

# vim: set syntax=sh:
