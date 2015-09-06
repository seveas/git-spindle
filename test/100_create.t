#!/bin/sh

test_description="Create new repos"

. ./setup.sh

test_expect_success "Clone source repos" "
    git clone https://github.com/seveas/whelk.git
    git clone https://github.com/seveas/hacks.git
"

test -d whelk || test_done

for spindle in hub lab bb; do 
    test_expect_success "Create repo ($spindle)" "
        ( cd whelk &&
        echo whelk > expected &&
        git_${spindle}_1 create &&
        git_${spindle}_1 repos | sed -e 's/ .*//' > actual &&
        test_cmp expected actual &&
        git_1 push $(echo $spindle | sed -e 's/^/git/' -e 's/gitbb/bitbucket/') refs/heads/*:refs/heads/* refs/tags/*:refs/tags/* )
    "
done;

test_expect_success "Creating a repo does not overwrite 'origin'" "
    cat >expected <<EOF &&
bitbucket	git@bitbucket.org:XXX/whelk.git (fetch)
bitbucket	git@bitbucket.org:XXX/whelk.git (push)
github	git@github.com:XXX/whelk.git (fetch)
github	git@github.com:XXX/whelk.git (push)
gitlab	git@gitlab.com:XXX/whelk.git (fetch)
gitlab	git@gitlab.com:XXX/whelk.git (push)
origin	https://github.com/seveas/whelk.git (fetch)
origin	https://github.com/seveas/whelk.git (push)
EOF
    git -C whelk remote -v > actual &&
    sort
    sed -e 's@:[^/]\\+/@:XXX/@' -i actual &&
    test_cmp expected actual
"

test_expect_success "Create a repo with a GitLab local install set as default" "
    host=\$(git_lab_local config host) &&
    user=\$(git_lab_local config user) &&
    token=\$(git_lab_local config token) &&
    echo \"\$host \$user \$token\" &&
    git_lab config host \$host &&
    git_lab config user \$user &&
    git_lab config token \$token &&
    (cd whelk && git_lab create)
"

for spindle in hub lab bb; do
    test_expect_success "Create repo with description ($spindle)" "
        ( cd hacks &&
        echo 'Hacks repo' > expected &&
        git_${spindle}_1 create -d 'Hacks repo' &&
        git_${spindle}_1 repos | sed -ne 's/.*H/H/p' > actual &&
        test_cmp expected actual )
    "
done;

test_expect_failure "Create private repo" "false"

test_done

# vim: set syntax=sh:
