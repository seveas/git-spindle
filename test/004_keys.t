#!/bin/sh

test_description="User information display test"

. ./setup.sh

test_expect_success "Generating keys" "
    ssh-keygen -trsa -N '' -f id_rsa -C git-spindle-test-key-1 -q &&
    mkdir .ssh &&
    ssh-keygen -trsa -N '' -f .ssh/id_rsa -C git-spindle-test-key-2 -q &&

    cat id_rsa.pub .ssh/id_rsa.pub | sort > expected
"

for spindle in hub lab bb; do test_expect_success "Add and retrieve keys ($spindle)" "
    git_${spindle}_1 add-public-keys &&
    git_${spindle}_1 public-keys > actual &&
    test_cmp .ssh/id_rsa.pub actual &&
    git_${spindle}_1 add-public-keys id_rsa.pub &&
    git_${spindle}_1 public-keys | sort > actual &&
    test_cmp expected actual
"; done

test_done

# vim: set syntax=sh:
