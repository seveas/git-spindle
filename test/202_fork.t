#!/bin/sh

test_description="Forking repositories"

. ./setup.sh

test_expect_success "Clone extra repos" "
    git clone https://$(spindle_host git_hub_)/seveas/hacks &&
    git clone https://$(spindle_host git_hub_)/seveas/python-hpilo &&
    git clone https://$(spindle_host git_hub_)/seveas/python-zonediff
"

for spindle in hub lab bb; do
    test_expect_success $spindle "Cleanup ($spindle)" "
        (export DEBUG=1; git_${spindle}_2 test-cleanup --repos)
    "
done

for spindle in hub lab bb; do
    test_expect_success $spindle "Create and prepare repos ($spindle)" "
        ( cd python-hpilo &&
        git_${spindle}_1 create &&
        git_1 push \$(spindle_remote git_${spindle}_1) refs/heads/*:refs/heads/* refs/tags/*:refs/tags/*) &&
        ( cd hacks &&
        git_${spindle}_1 set-origin &&
        git_1 push origin refs/heads/*:refs/heads/* refs/tags/*:refs/tags/* HEAD:branch-a HEAD:branch-b) &&
        ( cd python-zonediff &&
        git remote set-url origin git@$(spindle_host git_${spindle}_):$(spindle_namespace git${spindle}-test-1)/python-zonediff &&
        git_1 push origin refs/heads/*:refs/heads/* refs/tags/*:refs/tags/* HEAD:branch-a HEAD:branch-b)
    "
done

for spindle in hub lab bb; do
    test_expect_success $spindle "Forking already cloned repo ($spindle)" "
        ( cd python-hpilo &&
        git_${spindle}_1 set-origin &&
        git_${spindle}_2 fork &&
        git_${spindle}_2 repos | grep python-hpilo )
    "
done

for spindle in hub lab bb; do
    test_expect_success $spindle "Forking not-yet cloned repo ($spindle)" "
        rm -rf whelk &&
        src=\$(username git_${spindle}_1) &&
        git_${spindle}_2 fork \$src/whelk &&
        git_${spindle}_2 repos | grep whelk &&
        (cd whelk &&
        test_commit &&
        git_2 push &&
        echo -n 'Testing remote.pushDefault ... ' &&
        (git config remote.pushDefault && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.master.remote ... ' &&
        git config branch.master.remote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.master.pushRemote ... ' &&
        (git config branch.master.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo 'OK') &&
        rm -rf whelk
    "
done

for spindle in hub lab bb; do
    test_expect_success $spindle "Forking with triangular setup ($spindle)" "
        (cd hacks &&
        git_${spindle}_1 set-origin &&
        git_${spindle}_2 fork --triangular &&
        echo -n 'Testing remote.pushDefault ... ' &&
        git config remote.pushDefault >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.master.remote ... ' &&
        git config branch.master.remote >config &&
        grep -q 'upstream' config &&
        echo -n 'OK\nTesting branch.master.pushRemote ... ' &&
        git config branch.master.pushRemote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.master.merge ... ' &&
        git config branch.master.merge >config &&
        grep -q 'refs/heads/master' config &&
        echo 'OK')
    "
done

for spindle in hub lab bb; do
    test_expect_success $spindle "Forking with triangular setup and fixed upstream branch ($spindle)" "
        (cd python-zonediff &&
        git remote set-url origin git@$(spindle_host git_${spindle}_):$(spindle_namespace git${spindle}-test-1)/python-zonediff &&
        git_${spindle}_2 fork --triangular --upstream-branch=branch-a &&
        echo -n 'Testing remote.pushDefault ... ' &&
        git config remote.pushDefault >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.master.remote ... ' &&
        git config branch.master.remote >config &&
        grep -q 'upstream' config &&
        echo -n 'OK\nTesting branch.master.pushRemote ... ' &&
        git config branch.master.pushRemote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.master.merge ... ' &&
        git config branch.master.merge >config &&
        grep -q 'refs/heads/branch-a' config &&
        echo 'OK')
    "
done

for spindle in hub bb; do
    test_expect_success $spindle "Listing forks ($spindle)" "
        dst=\$(username git_${spindle}_1) &&
        dst=\$(username git_${spindle}_2) &&
        git_${spindle}_1 forks whelk >actual &&
        grep \$dst actual &&
        git_${spindle}_2 forks whelk >actual &&
        grep \$src actual
    "
done

test_expect_failure "Testing fork with extra clone options" "false"
test_expect_failure "Testing fork of a forked repo" "false"

test_done

# vim: set syntax=sh:
