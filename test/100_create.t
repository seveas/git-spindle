#!/bin/sh

test_description="Create new repos"

. ./setup.sh

test_expect_success "Clone source repo" "
    git clone https://github.com/seveas/whelk
"

test -d whelk || test_done

for spindle in hub lab bb; do 
    test_expect_success "Create repo ($spindle)" "
        ( cd whelk &&
        echo whelk > expected &&
        git_${spindle}_1 create &&
        git_${spindle}_1 repos | sed -e 's/ .*//' > actual &&
        test_cmp expected actual &&
        git_1 push -u origin refs/heads/*:refs/heads/* refs/tags/*:refs/tags/* )
    "
done;

test_expect_failure "Create repo with a description" "false"
test_expect_failure "Create private repo" "false"

test_done

# vim: set syntax=sh:
