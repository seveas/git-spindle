#!/bin/sh

test_description="User information display test"

. ./setup.sh

test_expect_success "whoami shows the current user" "
    git_lab_1 whoami | grep -q '^Profile.*/git-spindle-test-1' &&
    git_hub_1 whoami | grep -q '^Profile.*/git-spindle-test-1' &&
    git_bb_1  whoami | grep -q '^Profile.*/git-spindle-test-1'
"

test_expect_success "whois shows the expected user" "
    git_lab_1 whois git-spindle-test-2 | grep -q '^Profile.*/git-spindle-test-2' &&
    git_hub_1 whois git-spindle-test-2 | grep -q '^Profile.*/git-spindle-test-2' &&
    git_bb_1  whois git-spindle-test-2 | grep -q '^Profile.*/git-spindle-test-2'
"

test_done

# vim: set syntax=sh:
