#!/bin/sh

test_description="Managing repository access"

. ./setup.sh

test_expect_success hub "Managing GitHub access control" "
    rm -rf whelk &&
    git_hub_1 clone whelk &&
    (cd whelk &&
    echo $(username git_hub_1) > expected &&
    echo $(username git_hub_2) >> expected &&
    git_hub_1 add-collaborator $(username git_hub_2) &&
    git_hub_1 collaborators > actual &&
    test_cmp expected actual &&
    git_hub_1 remove-collaborator $(username git_hub_2) &&
    echo $(username git_hub_1) > expected &&
    git_hub_1 collaborators > actual &&
    test_cmp expected actual)
"

test_expect_success lab "Managing GitLab access control" "
    rm -rf whelk &&
    git_lab_1 clone whelk &&
    (cd whelk &&
    echo \"developer $(username git_lab_2)\" > expected &&
    echo \"reporter  $(username git_lab_3)\" >> expected &&
    git_lab_1 add-member $(username git_lab_2) &&
    git_lab_1 add-member --access-level=reporter $(username git_lab_3) &&
    git_lab_1 members > actual &&
    sed -e 's/ (.*//' -i actual &&
    test_cmp expected actual &&
    git_lab_1 remove-member $(username git_lab_2) &&
    git_lab_1 remove-member $(username git_lab_3) &&
    : > expected &&
    git_lab_1 members > actual &&
    sed -e 's/ (.*//' -i actual &&
    test_cmp expected actual)
"

test_expect_success bb "Managing BitBucket access control" "
    rm -rf whelk &&
    git_bb_1 clone whelk &&
    (cd whelk &&
    echo \"write $(username git_bb_3)\" > expected &&
    echo \"read  $(username git_bb_2)\" >> expected &&
    git_bb_1 add-privilege $(username git_bb_2) &&
    git_bb_1 add-privilege --write $(username git_bb_3) &&
    for attempt in 1 2 3 4 5; do
        git_bb_1 privileges > actual &&
        sed -e 's/ (.*//' -i actual &&
        { test_cmp expected actual && break; } || sleep 10
    done &&
    test_cmp expected actual &&
    git_bb_1 remove-privilege $(username git_bb_2) &&
    git_bb_1 remove-privilege $(username git_bb_3) &&
    : > expected &&
    git_bb_1 privileges > actual &&
    for attempt in 1 2 3 4 5; do
        git_bb_1 privileges > actual &&
        { test_cmp expected actual && break; } || sleep 10
    done)
"

test_done

# vim: set syntax=sh:
