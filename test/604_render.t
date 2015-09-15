#!/bin/sh

test_description="Testing markdown rendering"

. ./setup.sh

test_expect_success hub "Testing markdown rendering" "
    cat <<EOF >>test.md &&
Markdown rendering test
=======================
Hello, world!
EOF
    git_hub_1 render test.md > actual &&
    grep -q '^file://.*\\.html$' actual &&
    git_hub_1 render test.md --save test.html &&
    grep -q '<p>Hello, world!</p>' test.html
"
test_done

# vim: set syntax=sh:
