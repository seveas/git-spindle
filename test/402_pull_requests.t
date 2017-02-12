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
        git_${spindle}_2 clone --ssh python-hpilo
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
        grep -q $id-2 issues)
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
        grep -q $id-3 issues)
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
        grep -q $id-4 issues)
    "

    export FAKE_EDITOR_RESULT='editor-result'
    export FAKE_EDITOR_DATA="Pull request for the default upstream branch if not tracking anything $id-5\n\nThis is a pull request done by git-spindle's test suite\n"
    test_expect_success $spindle "Filing a pull request for the default upstream branch if not tracking anything ($spindle)" "
        (cd python-hpilo &&
        git_1 push -f upstream HEAD:pull-request-target &&
        git checkout --no-track -b pull-request-branch-4 upstream/pull-request-target &&
        test_commit &&
        git_2 push -f origin pull-request-branch-4 &&
        git_${spindle}_2 $pull-request &&
        grep -q ' into $(username git_${spindle}_1)/master$' editor-result &&
        git_${spindle}_2 issues --parent > issues &&
        grep -q $id-5 issues)
    "

    export FAKE_EDITOR_DATA="Pull request for the default upstream branch if tracking non-upstream $id-6\n\nThis is a pull request done by git-spindle's test suite\n"
    test_expect_success $spindle "Filing a pull request for the default upstream branch if tracking non-upstream ($spindle)" "
        (cd python-hpilo &&
        git_2 push -f origin HEAD:pull-request-target &&
        git checkout --track -b pull-request-branch-5 origin/pull-request-target &&
        test_commit &&
        git_2 push -f origin pull-request-branch-5 &&
        git_${spindle}_2 $pull-request &&
        grep -q ' into $(username git_${spindle}_1)/master$' editor-result &&
        git_${spindle}_2 issues --parent > issues &&
        grep -q $id-6 issues)
    "

    if [ $spindle != bb ]; then
        export FAKE_EDITOR_DATA="Pull request for the same source branch $id-8\n\nThis is a pull request done by git-spindle's test suite\n"
        test_expect_success $spindle "Filing a pull request twice for the same source branch saves the message and gives an error ($spindle)" "
            (cd python-hpilo &&
            git checkout -b pull-request-branch-7 upstream/master &&
            test_commit &&
            git_2 push -f origin pull-request-branch-7 &&
            git_${spindle}_2 $pull-request &&
            export FAKE_EDITOR_DATA='Pull request for the same source branch $id-9\n\nThis is a pull request done by git-spindle'\''s test suite\n' &&
            (git_${spindle}_2 $pull-request || true) > pr-output 2>&1 &&
            cat pr-output &&
            git_${spindle}_2 issues --parent > issues &&
            grep -q $id-8 issues &&
            ! grep -q $id-9 issues &&
            grep -q ' text has been saved in ' pr-output &&
            pr_output=\$(cat pr-output) &&
            grep -q '$id-9' \${pr_output##* })
        "
    fi

    export FAKE_EDITOR_DATA="Pull request for the tracked upstream branch $id-7\n\nThis is a pull request done by git-spindle's test suite\n"
    test_expect_success $spindle "Filing a pull request for the tracked upstream branch ($spindle)" "
        (cd python-hpilo &&
        git_1 push -f upstream HEAD:pull-request-target &&
        git checkout --track -b pull-request-branch-6 upstream/pull-request-target &&
        test_commit &&
        git_2 push -f origin pull-request-branch-6 &&
        git_${spindle}_2 $pull-request &&
        grep -q ' into $(username git_${spindle}_1)/pull-request-target$' editor-result &&
        git_${spindle}_2 issues --parent > issues &&
        grep -q $id-7 issues)
    "
done

test_expect_failure "Pull request with no commits" "false"
test_expect_failure "Turning an issue into a pull request" "false"
test_done

# vim: set syntax=sh:
