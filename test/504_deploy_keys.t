#!/bin/sh

test_description="Testing deploy keys"

. ./setup.sh

test_expect_success "Generating keys" "
    ssh-keygen -trsa -N '' -f deploy-key-1 -q &&
    ssh-keygen -trsa -N '' -f deploy-key-2 -q
"

test_expect_success hub "Testing deploy key manipulation (hub)" "
    rm -rf whelk &&
    git_hub_1 clone whelk &&
    (cd whelk &&
    git_hub_1 add-deploy-key ../deploy-key-1.pub &&
    git_hub_1 add-deploy-key --read-only ../deploy-key-2.pub &&
    git_hub_1 deploy-keys > actual &&
    sed -e 's/ (id: .*,/ (id: XXX,/' < actual > actual.sanitized &&
    echo \"\$(cat ../deploy-key-1.pub) (id: XXX, rw)\" > expected &&
    echo \"\$(cat ../deploy-key-2.pub) (id: XXX, ro)\" >> expected &&
    test_cmp expected actual.sanitized &&
    for key in \$(sed -e 's/.*id: \\(.*\\),.*/\\1/' < actual); do
    git_hub_1 remove-deploy-key \$key
    done &&
    git_hub_1 deploy-keys > actual &&
    : > expected &&
    test_cmp expected actual)
"

test_expect_success bb "Testing deploy key manipulation (bb)" "
    rm -rf whelk &&
    git_bb_1 clone whelk &&
    (cd whelk &&
    git_bb_1 add-deploy-key ../deploy-key-1.pub &&
    git_bb_1 deploy-keys > actual &&
    sed -e 's/ (id: .*)/ (id: XXX)/' < actual > actual.sanitized &&
    echo \"\$(cat ../deploy-key-1.pub) (id: XXX)\" > expected &&
    test_cmp expected actual.sanitized &&
    for key in \$(sed -e 's/.*id: \\(.*\\))/\\1/' < actual); do
    git_bb_1 remove-deploy-key \$key
    done &&
    git_bb_1 deploy-keys > actual &&
    : > expected &&
    test_cmp expected actual)
"

test_done

# vim: set syntax=sh:
