#!/bin/sh

test_description="Test the browse functionality"

. ./setup.sh

test_expect_success "Launch browsers for repo homepage" "
    cat >expected <<EOF &&
https://github.com/seveas/whelk
https://gitlab.com/seveas/whelk
https://bitbucket.org/seveas/whelk
EOF
    git_hub_1 browse seveas/whelk >actual &&
    git_lab_1 browse seveas/whelk >>actual &&
    git_bb_1 browse seveas/whelk >>actual &&
    test_cmp expected actual
"

test_expect_success "Launch browsers for repo issues page" "
    cat >expected <<EOF &&
https://github.com/seveas/whelk/issues
https://gitlab.com/seveas/whelk/issues
https://bitbucket.org/seveas/whelk/issues
EOF
    git_hub_1 browse seveas/whelk issues >actual &&
    git_lab_1 browse seveas/whelk issues >>actual &&
    git_bb_1 browse seveas/whelk issues >>actual &&
    test_cmp expected actual
"

test_expect_success "Launch browser from within a repo" "
    git_hub_1 clone seveas/whelk &&
    (cd whelk &&
    cat >expected <<EOF &&
https://github.com/seveas/whelk
https://github.com/seveas/whelk/issues
EOF
    git_hub_1 browse >actual &&
    git_hub_1 browse issues >>actual &&
    test_cmp expected actual )
"

test_done

# vim: set syntax=sh:
