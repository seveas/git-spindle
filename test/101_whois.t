#!/bin/sh

test_description="User information display test"

. ./setup.sh

for spindle in hub lab bb; do
    test_expect_success $spindle "whoami shows the current user ($spindle)" "
        git_${spindle}_1  whoami | grep -q '^Profile.*/$(username git_${spindle}_1)'
    "
    test_expect_success $spindle "whois shows the expected user ($spindle)" "
        git_${spindle}_1  whois $(username git_${spindle}_2) | grep -q '^Profile.*/$(username git_${spindle}_2)'
    "
done

test_done

# vim: set syntax=sh:
