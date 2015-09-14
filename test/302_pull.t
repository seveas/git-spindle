#!/bin/sh

test_description="Testing pull requests"

. ./setup.sh

id="$(bash -c 'echo $RANDOM')-$$"
export GIT_EDITOR=fake-editor
export FAKE_EDITOR_INCLUDE_ORIGINAL=1

for spindle in hub lab bb; do
    case $spindle in
        hub)
            pull=pull;;
        lab)
            pull=merge;;
        bb)
            pull=pull;;
    esac
    test_expect_success $spindle "Cloning source repo ($spindle)" "
        rm -rf python-hpilo &&
        git_${spindle}_2 clone python-hpilo
    "

    export FAKE_EDITOR_DATA="Pull request with single commit $id-1\n\nThis is a pull request done by git-spindle's test suite\n"
    test_expect_success $spindle "Filing a pull request with one commit ($spindle)" "
        (cd python-hpilo &&
        git reset --hard upstream/master &&
        test_commit &&
        git_2 push -f origin master &&
        git_${spindle}_2 $pull-request &&
        git_${spindle}_2 issues --parent > issues &&
        grep -q $id-1 issues)
    "

    export FAKE_EDITOR_DATA="Pull request with more than one commit $id-2\n\nThis is a pull request done by git-spindle's test suite\n"
    test_expect_success $spindle "Filing a pull request with more than one commit on a different branch ($spindle)" "
        (cd python-hpilo &&
        git checkout -b pull-request-branch upstream/master &&
        test_commit &&
        test_commit &&
        test_commit &&
        git_2 push -f -u origin pull-request-branch &&
        git checkout master &&
        git_${spindle}_2 $pull-request pull-request-branch:master &&
        git_${spindle}_2 issues --parent > issues &&
        grep -q $id-1 issues)
    "

    export FAKE_EDITOR_DATA="Pull request for unpushed branch $id-3\n\nThis is a pull request done by git-spindle's test suite\n"
    test_expect_success $spindle "Filing a pull request for an unpushed branch ($spindle)" "
        (cd python-hpilo &&
        git checkout -b pull-request-branch-2 upstream/master &&
        test_commit &&
        git_${spindle}_2 $pull-request --yes > pr-output &&
        cat pr-output &&
        grep 'does not exist' pr-output &&
        git_${spindle}_2 issues --parent > issues &&
        grep -q $id-1 issues)
    "

    export FAKE_EDITOR_DATA="Pull request for out-of-date branch $id-4\n\nThis is a pull request done by git-spindle's test suite\n"
    test_expect_success $spindle "Filing a pull request for an out-of-date branch ($spindle)" "
        (cd python-hpilo &&
        git checkout -b pull-request-branch-3 upstream/master &&
        test_commit &&
        git_2 push -f -u origin pull-request-branch-3
        test_commit &&
        git_${spindle}_2 $pull-request --yes > pr-output &&
        cat pr-output &&
        grep 'not up to date' pr-output &&
        git_${spindle}_2 issues --parent > issues &&
        grep -q $id-1 issues)
    "

done

test_expect_failure "Pull request with no commits" "false"
test_expect_failure "Turning an issue into a pull request" "false"
test_done

# vim: set syntax=sh:
