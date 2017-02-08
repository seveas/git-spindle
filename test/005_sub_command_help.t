#!/bin/sh

test_description="Testing git * help"

. ./setup.sh

test_expect_success "Testing help for unknown command" "
    echo 'Unknown command \"foo\"' > expected &&
    git_hub help foo > actual &&
    test_cmp expected actual
"

for spindle in hub lab bb; do
    test_expect_success "Testing help for known command ($spindle)" "
        echo 'Display the help for a command:' > expected &&
        echo '  git $spindle [options] help <command>' >> expected &&
        git_$spindle help help > actual &&
        test_cmp expected actual
    "
done

test_done

# vim: set syntax=sh:
