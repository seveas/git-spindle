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

    test_expect_success $spindle "List issues for a user, without being in a repo ($spindle)" "
        git_${spindle}_1 issues > issues &&
        grep -q whelk issues
    "

    case $spindle in
        bb)
            # Parent repo retrieval is currently broken for BB
            test_expect_failure $spindle "List issues for parent repos of a user, without being in a repo" "
                git_${spindle}_2 issues --parent > issues &&
                grep -q whelk issues &&
                grep -q 'Test issue (outside) $id' issues &&
                grep -q 'Test issue (inside) $id' issues
            "
            ;;
        *)
            test_expect_success $spindle "List issues for parent repos of a user, without being in a repo" "
                git_${spindle}_2 issues --parent > issues &&
                grep -q whelk issues &&
                grep -q 'Test issue (outside) $id' issues &&
                grep -q 'Test issue (inside) $id' issues
            "
            ;;
    esac

    test_expect_success $spindle "Display specific issue without naming repo explicitly ($spindle)" "
        (cd whelk &&
        git_${spindle}_1 issue 1 > issue &&
        grep -q '/1\\(/\\|\$\\)' issue)

    test_expect_success $spindle "Display non-existing issue ($spindle)" "
        git_${spindle}_1 issue whelk 999 > issue &&
        grep -q '^No issue with id 999 found in repository $(username git_${spindle}_1)/whelk$' issue
    "

    export FAKE_EDITOR_DATA="Test issue with umlaut ö $id\n\nThis is a test issue with umlaut ö done by git-spindle's test suite\n"
    test_expect_success $spindle "Display issue with special character in title and body ($spindle)" "
        (cd whelk &&
        LC_ALL=en_US.UTF-8 git_${spindle}_1 issue &&
        echo -n 'Testing with UTF-8 to make sure the issue was created correctly ... ' &&
        PYTHONIOENCODING=utf-8 git_${spindle}_1 issues > issues &&
        grep -q 'Test issue with umlaut ö $id' issues &&
        echo -n 'OK\nTesting with ascii to make sure the output escaping is done correctly ... ' &&
        PYTHONIOENCODING=ascii git_${spindle}_1 issues > issues &&
        grep -q 'Test issue with umlaut \\\\xf6 $id' issues &&
        echo 'OK')
    "

    test_expect_failure $spindle "Display single issue" "false"
done

test_done

# vim: set syntax=sh:
