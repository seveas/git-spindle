#!/bin/sh

test_description="Forking repositories"

. ./setup.sh

test_expect_success "Clone extra repository" "
    git clone https://github.com/seveas/python-hpilo
"

for spindle in hub lab bb; do
    test_expect_success $spindle "Cleanup ($spindle)" "
        (export DEBUG=1; git_${spindle}_2 test-cleanup --repos)
    "
done

for spindle in hub lab bb; do
    test_expect_success $spindle "Create repo ($spindle)" "
        ( cd python-hpilo &&
        git_${spindle}_1 create &&
        git_1 push \$(spindle_remote git_${spindle}_1) refs/heads/*:refs/heads/* refs/tags/*:refs/tags/* )
    "
done

for spindle in hub lab bb; do
    test_expect_success $spindle "Forking already cloned repo ($spindle)" "
        ( cd python-hpilo &&
        git_${spindle}_1 set-origin &&
        git_${spindle}_2 fork &&
        git_${spindle}_2 repos | grep python-hpilo )
    "
done

for spindle in hub lab bb; do
    test_expect_success $spindle "Forking not-yet cloned repo ($spindle)" "
        rm -rf whelk &&
        src=\$(username git_${spindle}_1) &&
        git_${spindle}_2 fork \$src/whelk &&
        git_${spindle}_2 repos | grep whelk &&
        (cd whelk &&
        test_commit &&
        git_2 push) &&
        rm -rf whelk
    "
done

for spindle in hub bb; do
    test_expect_success $spindle "Listing forks ($spindle)" "
        dst=\$(username git_${spindle}_1) &&
        dst=\$(username git_${spindle}_2) &&
        git_${spindle}_1 forks whelk >actual &&
        grep \$dst actual &&
        git_${spindle}_2 forks whelk >actual &&
        grep \$src actual
    "
done

test_expect_failure "Testing fork with extra clone options" "false"
test_expect_failure "Testing fork of a forked repo" "false"

test_done

# vim: set syntax=sh:
