#!/bin/sh

test_description="Testing set_origin"

. ./setup.sh

test_expect_success "Cloning repository" "
    git clone https://github.com/seveas/whelk &&
    git -C whelk remote remove origin
"

for spindle in lab hub bb; do
    test_expect_success $spindle "Setting triangular origin to $spindle" "
        (cd whelk &&
        host=\$(spindle_host git_${spindle}_2) &&
        ( git branch --unset-upstream master || true ) &&
        git_${spindle}_2 set-origin --triangular &&
        git remote -v &&
        git config remote.origin.url | grep -q git@\$host &&
        git config remote.upstream.url | grep -q \"https://\\(.*@\\)\\?\$host\" &&
        git config branch.master.remote | grep -q \"upstream\" &&
        git config branch.master.pushremote | grep -q \"origin\")
    "
done

for spindle in lab hub bb; do
    test_expect_success $spindle "Setting origin to $spindle" "
        (cd whelk &&
        host=\$(spindle_host git_${spindle}_2) &&
        ( git branch --unset-upstream master || true ) &&
        git_${spindle}_2 set-origin &&
        git remote -v &&
        git config remote.origin.url | grep -q git@\$host &&
        git config remote.upstream.url | grep -q \"https://\\(.*@\\)\\?\$host\" &&
        git config branch.master.remote | grep -q \"origin\")
    "
done

for spindle in lab hub bb; do
    for protocol in ssh http git; do
        case $spindle-$protocol in
            lab-git)
                continue;;
            bb-git)
                continue;;
           *-ssh)
                scheme=git@;;
           *-http)
                scheme="https://\\(.*@\\)\\?";;
           *-git)
                scheme=git://;;
        esac
        test_expect_success $spindle "Setting origin to $spindle ($protocol)" "
            (cd whelk &&
            host=\$(spindle_host git_${spindle}_2) &&
            git_${spindle}_2 set-origin --$protocol &&
            git remote -v &&
            git config remote.origin.url | grep -q \"^$scheme\$host\" &&
            git config remote.upstream.url | grep -q \"^$scheme\$host\")
        "
    done
done

test_expect_success lab_local "Setting origin (local gitlab)" "
    (cd whelk &&
    host=\$(spindle_host git_lab_local) &&
    git_lab_local set-origin &&
    git remote -v &&
    git config remote.origin.url | grep -q \$host)
"
test_done

# vim: set syntax=sh:
