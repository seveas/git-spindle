#!/bin/sh

test_description="Clone repositories"

. ./setup.sh

for spindle in hub lab bb; do
    test_expect_success $spindle "Clone repo ($spindle)" "
        src=\$(username git_${spindle}_1) &&
        git_${spindle}_2 clone --ssh \$src/whelk whelk-$spindle-ssh &&
        test -d whelk-$spindle-ssh &&
        git_${spindle}_2 clone --http \$src/whelk whelk-$spindle-http &&
        test -d whelk-$spindle-http
    "

    test_expect_success $spindle "Clone with extra args ($spindle)" "
        git_${spindle}_1 clone --bare whelk &&
        test -d whelk.git &&
        rm -rf whelk.git
    "

    test_expect_success $spindle "Clone parent repo ($spindle)" "
        src=\$(username git_${spindle}_2) &&
        git_${spindle}_1 clone --parent \$src/whelk &&
        ! grep \$src whelk/.git/config &&
        rm -rf whelk
    "
done;


test_expect_failure "Test cloning where name != slug" "false"

test_done

# vim: set syntax=sh:
