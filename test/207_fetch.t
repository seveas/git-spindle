#!/bin/sh

test_description="Testing fetch"

. ./setup.sh

for spindle in hub lab bb; do
    src=$(username git_${spindle}_2)
    test_expect_success $spindle "Testing bare fetch ($spindle)" "
        rm -rf python-hpilo &&
        git_${spindle}_1 clone python-hpilo &&
        (cd python-hpilo &&
        git_${spindle}_1 fetch $src &&
        git branch -r | grep $src/master)
    "
    test_expect_success $spindle "Testing fetch with branchname ($spindle)" "
        (cd python-hpilo &&
        git for-each-ref refs/remotes/$src | xargs -n1 git update-ref -d
        git branch -a > expected &&
        echo remotes/$src/master >> expected &&
        git_${spindle}_1 fetch $src master &&
        git branch -r | grep $src/master)
    "
    test_expect_success $spindle "Testing fetch with refspec ($spindle)" "
        (cd python-hpilo &&
        git for-each-ref refs/remotes/$src | xargs -n1 git update-ref -d
        git_${spindle}_1 fetch $src master:$src-test &&
        git branch grep $src-test)
    "
done

test_done

# vim: set syntax=sh:
