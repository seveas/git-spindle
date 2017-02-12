#!/bin/sh

test_description="Testing message templates"

. ./setup.sh

id="$(bash -c 'echo $RANDOM')-$$"
export GIT_EDITOR=fake-editor
export FAKE_EDITOR_INCLUDE_ORIGINAL=1
unset FAKE_EDITOR_DATA

test_expect_success hub "Cloning source repo" "
    rm -rf python-hpilo &&
    git_hub_2 clone --ssh python-hpilo
"

test_expect_success hub "Preparing target repo" "
    (cd python-hpilo &&
    git reset --hard upstream/master &&
    git checkout HEAD^0 &&
    echo 'Test issue template $id-1\n\nThis is a test issue done by git-spindle'\''s test suite\n' > ISSUE_TEMPLATE &&
    echo 'Test pull request template $id-2\n\nThis is a pull request done by git-spindle'\''s test suite\n' > PULL_REQUEST_TEMPLATE &&
    git add ISSUE_TEMPLATE PULL_REQUEST_TEMPLATE &&
    test_commit &&
    git_1 push -f upstream HEAD:master)
"

test_expect_success hub "Filing an issue with issue template to parent repo" "
    (cd python-hpilo &&
    git_hub_2 issue --parent &&
    git_hub_2 issues --parent > issues &&
    grep -q ' issue template $id-1 ' issues)
"

export FAKE_EDITOR_DATA="Pull request with pull request template $id-2\n\n"
test_expect_success hub "Filing a pull request with pull request template in the target repo" "
    (cd python-hpilo &&
    git checkout -b pull-request-branch-8 master &&
    test_commit &&
    git_2 push -f origin pull-request-branch-8 &&
    git_hub_2 pull-request pull-request-branch-8:master &&
    git_hub_2 issues --parent > issues &&
    issues=\$(grep $id-2 issues) &&
    issue_id=\"\${issues#[}\" &&
    issue_id=\"\${issue_id%%]*}\" &&
    git_hub_2 issue --parent python-hpilo \$issue_id > issue &&
    grep -q ' pull request template $id-2$' issue)
"

test_done

# vim: set syntax=sh:
