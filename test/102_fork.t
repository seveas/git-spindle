#!/bin/sh

test_description="Forking repositories"

. ./setup.sh

test_expect_success "Clone extra repository" "
    git clone https://github.com/seveas/python-hpilo
"

test -d python-hpilo || test_done

for spindle in hub lab bb; do 
    test_expect_success "Create repo ($spindle)" "
        ( cd python-hpilo &&
        git_${spindle}_1 create &&
        git_1 push -u origin refs/heads/*:refs/heads/* refs/tags/*:refs/tags/* )
    "
done

for spindle in hub lab bb; do 
    test_expect_success "Forking already cloned repo ($spindle)" "
        ( cd python-hpilo &&
        git_${spindle}_1 set-origin &&
        git_${spindle}_2 fork &&
        git_${spindle}_2 repos | grep python-hpilo )
    "
done

for spindle in hub lab bb; do 
    test_expect_success "Forking not-yet cloned repo ($spindle)" "
        src=\$(export DEBUG=1; git_${spindle}_1 run-shell -c 'print(self.my_login)') &&
        git_${spindle}_2 fork \$src/whelk &&
        git_${spindle}_2 repos | grep whelk &&
        (cd whelk &&
        test_commit &&
        git_2 push) &&
        rm -rf whelk
    "
done

for spindle in hub bb; do 
    test_expect_success "Listing forks" "
        dst=\$(export DEBUG=1; git_${spindle}_1 run-shell -c 'print(self.my_login)') &&
        dst=\$(export DEBUG=1; git_${spindle}_2 run-shell -c 'print(self.my_login)') &&
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
