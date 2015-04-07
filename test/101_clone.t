#!/bin/sh

test_description="Clone repositories"

. ./setup.sh

for spindle in hub lab bb; do 
    test_expect_success "Clone repo ($spindle)" "
        src=\$(export DEBUG=1; git_${spindle}_1 run-shell -c 'print(self.my_login)') &&
        git_${spindle}_2 clone --ssh \$src/whelk whelk-$spindle-ssh &&
        test -d whelk-$spindle-ssh &&
        git_${spindle}_2 clone --http \$src/whelk whelk-$spindle-http &&
        test -d whelk-$spindle-http
    "
done;

test_expect_success "Clone with extra args" "
    git_${spindle}_1 clone --bare whelk &&
    test -d whelk.git
"

test_expect_failure "Test cloning where name != slug" "false"
test_expect_failure "Test cloning with --parent" "false"

test_done

# vim: set syntax=sh:
