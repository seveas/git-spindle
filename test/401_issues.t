#!/bin/sh

test_description="Testing issues"

. ./setup.sh

id="$(bash -c 'echo $RANDOM')-$$"

test_expect_success "Cloning source repo" "
    git clone http://github.com/seveas/whelk
"

export GIT_EDITOR=fake-editor

for spindle in lab hub bb; do

    test_expect_success $spindle "Setting repo origin ($spindle)" "
        (cd whelk &&
        git_${spindle}_1 set-origin)
    "

    export FAKE_EDITOR_DATA="Test issue (outside) $id\n\nThis is a test issue done by git-spindle's test suite\n"
    test_expect_success $spindle "Filing an issue outside a repo ($spindle)" "
        git_${spindle}_1 issue whelk
    "

    export FAKE_EDITOR_DATA="Test issue (inside) $id\n\nThis is a test issue done by git-spindle's test suite\n"
    test_expect_success $spindle "Filing an issue inside a repo ($spindle)" "
        (cd whelk &&
        git_${spindle}_1 issue)
    "

    test_expect_success $spindle "Listing issues outside the repo ($spindle)" "
        git_${spindle}_1 issues whelk > issues &&
        grep -q 'Test issue (outside) $id' issues &&
        grep -q 'Test issue (inside) $id' issues
    "

    test_expect_success $spindle "Listing issues inside the repo ($spindle)" "
        (cd whelk &&
        git_${spindle}_1 issues whelk > issues &&
        grep -q 'Test issue (outside) $id' issues &&
        grep -q 'Test issue (inside) $id' issues)
    "

    test_expect_success $spindle "List issues for a user, without being in a repo" "
        git_${spindle}_1 issues > issues &&
        grep -q whelk issues
    "

    test_expect_failure $spindle "Display single issue" "false"
done

test_done

# vim: set syntax=sh:
