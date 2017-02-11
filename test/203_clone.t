#!/bin/sh

test_description="Clone repositories"

. ./setup.sh

test_expect_success REMOTE "Clone reference repository" "
    git clone https://$(spindle_host git_hub_)/seveas/whelk whelk-ref
"

for spindle in hub lab bb; do
    test_expect_success $spindle "Clone repo ($spindle)" "
        src=\$(username git_${spindle}_1) &&
        git_${spindle}_2 clone --ssh \$src/whelk whelk-$spindle-ssh &&
        test -d whelk-$spindle-ssh &&
        git_${spindle}_2 clone --http \$src/whelk whelk-$spindle-http &&
        test -d whelk-$spindle-http
    "

    test_expect_success $spindle "Clone with extra args ($spindle)" "
        git_${spindle}_1 clone --bare whelk &&
        test -d whelk.git &&
        rm -rf whelk.git
    "

    test_expect_success $spindle "Clone parent repo ($spindle)" "
        src=\$(username git_${spindle}_2) &&
        git_${spindle}_1 clone --parent \$src/whelk &&
        ! grep \$src whelk/.git/config &&
        rm -rf whelk
    "

    test_expect_success $spindle "Prepare repos ($spindle)" "
        cp -a whelk-ref whelk &&
        (cd whelk &&
        git_${spindle}_2 set-origin --ssh &&
        git_1 push -f upstream HEAD:git-1-branch HEAD:git-1-and-2-branch &&
        git_2 push -f origin HEAD:git-2-branch HEAD:git-1-and-2-branch) &&
        rm -rf whelk
    "

    test_expect_success $spindle "Clone non-fork non-triangularly ($spindle)" "
        rm -rf whelk &&
        git_${spindle}_1 clone --reference whelk-ref --branch git-1-and-2-branch whelk &&
        (cd whelk &&
        echo -n 'Testing remote.pushDefault ... ' &&
        (git config remote.pushDefault && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.remote ... ' &&
        git config branch.git-1-and-2-branch.remote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.pushRemote ... ' &&
        (git config branch.git-1-and-2-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.merge ... ' &&
        git config branch.git-1-and-2-branch.merge >config &&
        grep -q 'refs/heads/git-1-and-2-branch' config &&
        echo 'OK') &&
        rm -rf whelk
    "

    test_expect_success $spindle "Clone fork non-triangularly ($spindle)" "
        rm -rf whelk &&
        git_${spindle}_2 clone --reference whelk-ref --branch git-1-and-2-branch whelk &&
        (cd whelk &&
        echo -n 'Testing remote.pushDefault ... ' &&
        (git config remote.pushDefault && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.remote ... ' &&
        git config branch.git-1-and-2-branch.remote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.pushRemote ... ' &&
        (git config branch.git-1-and-2-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.merge ... ' &&
        git config branch.git-1-and-2-branch.merge >config &&
        grep -q 'refs/heads/git-1-and-2-branch' config &&
        echo 'OK') &&
        rm -rf whelk
    "

    test_expect_success $spindle "Clone non-fork triangularly ($spindle)" "
        rm -rf whelk &&
        git_${spindle}_1 clone --triangular --reference whelk-ref --branch git-1-and-2-branch whelk &&
        (cd whelk &&
        echo -n 'Testing remote.pushDefault ... ' &&
        (git config remote.pushDefault && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.remote ... ' &&
        git config branch.git-1-and-2-branch.remote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.pushRemote ... ' &&
        (git config branch.git-1-and-2-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.merge ... ' &&
        git config branch.git-1-and-2-branch.merge >config &&
        grep -q 'refs/heads/git-1-and-2-branch' config &&
        echo 'OK') &&
        rm -rf whelk
    "

    test_expect_success $spindle "Clone fork triangularly ($spindle)" "
        rm -rf whelk &&
        git_${spindle}_2 clone --triangular --reference whelk-ref --branch git-1-and-2-branch whelk &&
        (cd whelk &&
        echo -n 'Testing remote.pushDefault ... ' &&
        git config remote.pushDefault >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.remote ... ' &&
        git config branch.git-1-and-2-branch.remote >config &&
        grep -q 'upstream' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.pushRemote ... ' &&
        git config branch.git-1-and-2-branch.pushRemote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.merge ... ' &&
        git config branch.git-1-and-2-branch.merge >config &&
        grep -q 'refs/heads/git-1-and-2-branch' config &&
        echo 'OK') &&
        rm -rf whelk
    "

    test_expect_success $spindle "Clone non-fork triangularly with fixed upstream branch ($spindle)" "
        rm -rf whelk &&
        git_${spindle}_1 clone --triangular --upstream-branch master --reference whelk-ref --branch git-1-and-2-branch whelk &&
        (cd whelk &&
        echo -n 'Testing remote.pushDefault ... ' &&
        (git config remote.pushDefault && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.remote ... ' &&
        git config branch.git-1-and-2-branch.remote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.pushRemote ... ' &&
        (git config branch.git-1-and-2-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.merge ... ' &&
        git config branch.git-1-and-2-branch.merge >config &&
        grep -q 'refs/heads/git-1-and-2-branch' config &&
        echo 'OK') &&
        rm -rf whelk
    "

    test_expect_success $spindle "Clone fork triangularly with fixed upstream branch ($spindle)" "
        rm -rf whelk &&
        git_${spindle}_2 clone --triangular --upstream-branch master --reference whelk-ref --branch git-1-and-2-branch whelk &&
        (cd whelk &&
        echo -n 'Testing remote.pushDefault ... ' &&
        git config remote.pushDefault >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.remote ... ' &&
        git config branch.git-1-and-2-branch.remote >config &&
        grep -q 'upstream' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.pushRemote ... ' &&
        git config branch.git-1-and-2-branch.pushRemote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.merge ... ' &&
        git config branch.git-1-and-2-branch.merge >config &&
        grep -q 'refs/heads/master' config &&
        echo 'OK') &&
        rm -rf whelk
    "

    test_expect_success $spindle "Clone non-fork triangularly with non-existing fixed upstream branch ($spindle)" "
        rm -rf whelk &&
        git_${spindle}_1 clone --triangular --upstream-branch non-existing-branch --reference whelk-ref --branch git-1-and-2-branch whelk &&
        (cd whelk &&
        echo -n 'Testing remote.pushDefault ... ' &&
        (git config remote.pushDefault && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.remote ... ' &&
        git config branch.git-1-and-2-branch.remote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.pushRemote ... ' &&
        (git config branch.git-1-and-2-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.merge ... ' &&
        git config branch.git-1-and-2-branch.merge >config &&
        grep -q 'refs/heads/git-1-and-2-branch' config &&
        echo 'OK') &&
        rm -rf whelk
    "

    test_expect_success $spindle "Clone fork triangularly with non-existing fixed upstream branch ($spindle)" "
        rm -rf whelk &&
        git_${spindle}_2 clone --triangular --upstream-branch non-existing-branch --reference whelk-ref --branch git-1-and-2-branch whelk &&
        (cd whelk &&
        echo -n 'Testing remote.pushDefault ... ' &&
        git config remote.pushDefault >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.remote ... ' &&
        git config branch.git-1-and-2-branch.remote >config &&
        grep -q 'upstream' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.pushRemote ... ' &&
        git config branch.git-1-and-2-branch.pushRemote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.merge ... ' &&
        git config branch.git-1-and-2-branch.merge >config &&
        grep -q 'refs/heads/git-1-and-2-branch' config &&
        echo 'OK') &&
        rm -rf whelk
    "
done;


test_expect_failure "Test cloning where name != slug" "false"

test_done

# vim: set syntax=sh:
