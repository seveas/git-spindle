#!/bin/sh

test_description="Testing git * config"

. ./setup.sh

test_expect_success "Testing config setting" "
    git_hub_1 config level over_9000 &&
    test \$(git_hub_1 config level) = over_9000
"
test_expect_success "Config should not taint other accounts" "
    test -z \"\$(git_hub_2 config level)\"
"
test_expect_success "Testing config unsetting" "
    git_hub_1 config --unset level &&
    test -z \"\$(git_hub_1 config level)\"
"

test_done

# vim: set syntax=sh:
