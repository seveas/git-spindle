#!/bin/sh

test_description="Testing branch protections"

. ./setup.sh

test_expect_success lab "Cloning source repo" "
    git_lab_1 clone whelk
"

test_expect_success lab "Master is protected by default" "
    (cd whelk &&
    git_lab_1 protected > actual &&
    echo master > expected &&
    test_cmp expected actual)
"

test_expect_success lab "Unprotect and reprotect master" "
    (cd whelk &&
    git_lab_1 unprotect master &&
    git_lab_1 protected > actual &&
    : > expected &&
    test_cmp expected actual &&
    git_lab_1 protect master &&
    git_lab_1 protected > actual &&
    echo master > expected &&
    test_cmp expected actual)
"

test_expect_success lab "Protect and unprotect secondary branch" "
    (cd whelk &&
    git_lab_1 protect debian &&
    git_lab_1 protected > actual &&
    echo debian > expected &&
    echo master >> expected &&
    test_cmp expected actual &&
    git_lab_1 unprotect debian &&
    git_lab_1 protected > actual &&
    echo master > expected &&
    test_cmp expected actual)
"

test_done

# vim: set syntax=sh:
