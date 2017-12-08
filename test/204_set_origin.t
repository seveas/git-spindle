#!/bin/sh

test_description="Testing set_origin"

. ./setup.sh

test_expect_success "Cloning repository" "
    git clone https://$(spindle_host git_hub_)/seveas/whelk whelk-src &&
    (cd whelk-src &&
    git remote remove origin &&
    git branch git-1-branch &&
    git branch git-2-branch &&
    git branch git-1-and-2-branch &&
    git branch local-branch)
"

for spindle in lab hub bb; do
    test_expect_success $spindle "Prepare repos ($spindle)" "
        rm -rf whelk &&
        cp -a whelk-src whelk &&
        (cd whelk &&
        git_${spindle}_2 set-origin --ssh &&
        git_1 push -f upstream git-1-branch git-1-and-2-branch &&
        git_2 push -f origin git-2-branch git-1-and-2-branch)
    "
done

for spindle in lab hub bb; do
    test_expect_success $spindle "Setting non-fork origin non-triangularly to $spindle" "
        rm -rf whelk &&
        cp -a whelk-src whelk &&
        (cd whelk &&
        git_${spindle}_1 set-origin &&
        git remote -v &&
        host=$(spindle_host git_${spindle}_1) &&
        echo -n 'Testing remote.origin.url ... ' &&
        git config remote.origin.url >config &&
        grep -q git@\$host config &&
        echo -n 'OK\nTesting remote.upstream.url ... ' &&
        (git config remote.upstream.url && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting remote.pushDefault ... ' &&
        (git config remote.pushDefault && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-branch.remote ... ' &&
        git config branch.git-1-branch.remote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-branch.merge ... ' &&
        git config branch.git-1-branch.merge >config &&
        grep -q 'refs/heads/git-1-branch' config &&
        echo -n 'OK\nTesting branch.git-1-branch.pushRemote ... ' &&
        (git config branch.git-1-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-2-branch.remote ... ' &&
        (git config branch.git-2-branch.remote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-2-branch.merge ... ' &&
        (git config branch.git-2-branch.merge && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-2-branch.pushRemote ... ' &&
        (git config branch.git-2-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.remote ... ' &&
        git config branch.git-1-and-2-branch.remote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.merge ... ' &&
        git config branch.git-1-and-2-branch.merge >config &&
        grep -q 'refs/heads/git-1-and-2-branch' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.pushRemote ... ' &&
        (git config branch.git-1-and-2-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.local-branch.remote ... ' &&
        (git config branch.local-branch.remote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.local-branch.merge ... ' &&
        (git config branch.local-branch.merge && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.local-branch.pushRemote ... ' &&
        (git config branch.local-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo 'OK')
    "
done

for spindle in lab hub bb; do
    test_expect_success $spindle "Setting fork origin non-triangularly to $spindle" "
        rm -rf whelk &&
        cp -a whelk-src whelk &&
        (cd whelk &&
        git_${spindle}_2 set-origin &&
        git remote -v &&
        host=$(spindle_host git_${spindle}_2) &&
        echo -n 'Testing remote.origin.url ... ' &&
        git config remote.origin.url >config &&
        grep -q git@\$host config &&
        echo -n 'OK\nTesting remote.upstream.url ... ' &&
        git config remote.upstream.url >config &&
        grep -q \"https://\\(.*@\\)\\?\$host\" config &&
        echo -n 'OK\nTesting remote.pushDefault ... ' &&
        (git config remote.pushDefault && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-branch.remote ... ' &&
        (git config branch.git-1-branch.remote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-branch.merge ... ' &&
        (git config branch.git-1-branch.merge && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-branch.pushRemote ... ' &&
        (git config branch.git-1-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-2-branch.remote ... ' &&
        git config branch.git-2-branch.remote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-2-branch.merge ... ' &&
        git config branch.git-2-branch.merge >config &&
        grep -q 'refs/heads/git-2-branch' config &&
        echo -n 'OK\nTesting branch.git-2-branch.pushRemote ... ' &&
        (git config branch.git-2-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.remote ... ' &&
        git config branch.git-1-and-2-branch.remote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.merge ... ' &&
        git config branch.git-1-and-2-branch.merge >config &&
        grep -q 'refs/heads/git-1-and-2-branch' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.pushRemote ... ' &&
        (git config branch.git-1-and-2-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.local-branch.remote ... ' &&
        (git config branch.local-branch.remote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.local-branch.merge ... ' &&
        (git config branch.local-branch.merge && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.local-branch.pushRemote ... ' &&
        (git config branch.local-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo 'OK')
    "
done

for spindle in lab hub bb; do
    test_expect_success $spindle "Setting non-fork origin triangularly to $spindle" "
        rm -rf whelk &&
        cp -a whelk-src whelk &&
        (cd whelk &&
        git_${spindle}_1 set-origin --triangular &&
        git remote -v &&
        host=$(spindle_host git_${spindle}_1) &&
        echo -n 'Testing remote.origin.url ... ' &&
        git config remote.origin.url >config &&
        grep -q git@\$host config &&
        echo -n 'OK\nTesting remote.upstream.url ... ' &&
        (git config remote.upstream.url && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting remote.pushDefault ... ' &&
        git config remote.pushDefault >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-branch.remote ... ' &&
        git config branch.git-1-branch.remote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-branch.merge ... ' &&
        git config branch.git-1-branch.merge >config &&
        grep -q 'refs/heads/git-1-branch' config &&
        echo -n 'OK\nTesting branch.git-1-branch.pushRemote ... ' &&
        git config branch.git-1-branch.pushRemote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-2-branch.remote ... ' &&
        (git config branch.git-2-branch.remote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-2-branch.merge ... ' &&
        (git config branch.git-2-branch.merge && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-2-branch.pushRemote ... ' &&
        (git config branch.git-2-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.remote ... ' &&
        git config branch.git-1-and-2-branch.remote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.merge ... ' &&
        git config branch.git-1-and-2-branch.merge >config &&
        grep -q 'refs/heads/git-1-and-2-branch' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.pushRemote ... ' &&
        git config branch.git-1-and-2-branch.pushRemote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.local-branch.remote ... ' &&
        (git config branch.local-branch.remote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.local-branch.merge ... ' &&
        (git config branch.local-branch.merge && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.local-branch.pushRemote ... ' &&
        (git config branch.local-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo 'OK')
    "
done

for spindle in lab hub bb; do
    test_expect_success $spindle "Setting fork origin triangularly to $spindle" "
        rm -rf whelk &&
        cp -a whelk-src whelk &&
        (cd whelk &&
        git_${spindle}_2 set-origin --triangular &&
        git remote -v &&
        host=$(spindle_host git_${spindle}_2) &&
        echo -n 'Testing remote.origin.url ... ' &&
        git config remote.origin.url >config &&
        grep -q git@\$host config &&
        echo -n 'OK\nTesting remote.upstream.url ... ' &&
        git config remote.upstream.url >config &&
        grep -q \"https://\\(.*@\\)\\?\$host\" config &&
        echo -n 'OK\nTesting remote.pushDefault ... ' &&
        git config remote.pushDefault >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-branch.remote ... ' &&
        git config branch.git-1-branch.remote >config &&
        grep -q 'upstream' config &&
        echo -n 'OK\nTesting branch.git-1-branch.merge ... ' &&
        git config branch.git-1-branch.merge >config &&
        grep -q 'refs/heads/git-1-branch' config &&
        echo -n 'OK\nTesting branch.git-1-branch.pushRemote ... ' &&
        (git config branch.git-1-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-2-branch.remote ... ' &&
        git config branch.git-2-branch.remote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-2-branch.merge ... ' &&
        git config branch.git-2-branch.merge >config &&
        grep -q 'refs/heads/git-2-branch' config &&
        echo -n 'OK\nTesting branch.git-2-branch.pushRemote ... ' &&
        git config branch.git-2-branch.pushRemote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.remote ... ' &&
        git config branch.git-1-and-2-branch.remote >config &&
        grep -q 'upstream' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.merge ... ' &&
        git config branch.git-1-and-2-branch.merge >config &&
        grep -q 'refs/heads/git-1-and-2-branch' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.pushRemote ... ' &&
        git config branch.git-1-and-2-branch.pushRemote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.local-branch.remote ... ' &&
        (git config branch.local-branch.remote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.local-branch.merge ... ' &&
        (git config branch.local-branch.merge && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.local-branch.pushRemote ... ' &&
        (git config branch.local-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo 'OK')
    "
done

for spindle in lab hub bb; do
    test_expect_success $spindle "Setting non-fork origin triangularly with fixed upstream branch to $spindle" "
        rm -rf whelk &&
        cp -a whelk-src whelk &&
        (cd whelk &&
        git_${spindle}_1 set-origin --triangular --upstream-branch master &&
        git remote -v &&
        host=$(spindle_host git_${spindle}_1) &&
        echo -n 'Testing remote.origin.url ... ' &&
        git config remote.origin.url >config &&
        grep -q git@\$host config &&
        echo -n 'OK\nTesting remote.upstream.url ... ' &&
        (git config remote.upstream.url && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting remote.pushDefault ... ' &&
        git config remote.pushDefault >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-branch.remote ... ' &&
        git config branch.git-1-branch.remote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-branch.merge ... ' &&
        git config branch.git-1-branch.merge >config &&
        grep -q 'refs/heads/git-1-branch' config &&
        echo -n 'OK\nTesting branch.git-1-branch.pushRemote ... ' &&
        git config branch.git-1-branch.pushRemote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-2-branch.remote ... ' &&
        (git config branch.git-2-branch.remote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-2-branch.merge ... ' &&
        (git config branch.git-2-branch.merge && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-2-branch.pushRemote ... ' &&
        (git config branch.git-2-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.remote ... ' &&
        git config branch.git-1-and-2-branch.remote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.merge ... ' &&
        git config branch.git-1-and-2-branch.merge >config &&
        grep -q 'refs/heads/git-1-and-2-branch' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.pushRemote ... ' &&
        git config branch.git-1-and-2-branch.pushRemote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.local-branch.remote ... ' &&
        (git config branch.local-branch.remote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.local-branch.merge ... ' &&
        (git config branch.local-branch.merge && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.local-branch.pushRemote ... ' &&
        (git config branch.local-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo 'OK')
    "
done

for spindle in lab hub bb; do
    test_expect_success $spindle "Setting fork origin triangularly with fixed upstream branch to $spindle" "
        rm -rf whelk &&
        cp -a whelk-src whelk &&
        (cd whelk &&
        git_${spindle}_2 set-origin --triangular --upstream-branch master &&
        git remote -v &&
        host=$(spindle_host git_${spindle}_2) &&
        echo -n 'Testing remote.origin.url ... ' &&
        git config remote.origin.url >config &&
        grep -q git@\$host config &&
        echo -n 'OK\nTesting remote.upstream.url ... ' &&
        git config remote.upstream.url >config &&
        grep -q \"https://\\(.*@\\)\\?\$host\" config &&
        echo -n 'OK\nTesting remote.pushDefault ... ' &&
        git config remote.pushDefault >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-branch.remote ... ' &&
        git config branch.git-1-branch.remote >config &&
        grep -q 'upstream' config &&
        echo -n 'OK\nTesting branch.git-1-branch.merge ... ' &&
        git config branch.git-1-branch.merge >config &&
        grep -q 'refs/heads/master' config &&
        echo -n 'OK\nTesting branch.git-1-branch.pushRemote ... ' &&
        (git config branch.git-1-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-2-branch.remote ... ' &&
        git config branch.git-2-branch.remote >config &&
        grep -q 'upstream' config &&
        echo -n 'OK\nTesting branch.git-2-branch.merge ... ' &&
        git config branch.git-2-branch.merge >config &&
        grep -q 'refs/heads/master' config &&
        echo -n 'OK\nTesting branch.git-2-branch.pushRemote ... ' &&
        git config branch.git-2-branch.pushRemote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.remote ... ' &&
        git config branch.git-1-and-2-branch.remote >config &&
        grep -q 'upstream' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.merge ... ' &&
        git config branch.git-1-and-2-branch.merge >config &&
        grep -q 'refs/heads/master' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.pushRemote ... ' &&
        git config branch.git-1-and-2-branch.pushRemote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.local-branch.remote ... ' &&
        git config branch.local-branch.remote >config &&
        grep -q 'upstream' config &&
        echo -n 'OK\nTesting branch.local-branch.merge ... ' &&
        git config branch.local-branch.merge >config &&
        grep -q 'refs/heads/master' config &&
        echo -n 'OK\nTesting branch.local-branch.pushRemote ... ' &&
        (git config branch.local-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo 'OK')
    "
done

for spindle in lab hub bb; do
    test_expect_success $spindle "Setting non-fork origin triangularly with non-existing fixed upstream branch to $spindle" "
        rm -rf whelk &&
        cp -a whelk-src whelk &&
        (cd whelk &&
        git_${spindle}_1 set-origin --triangular --upstream-branch non-existing-branch &&
        git remote -v &&
        host=$(spindle_host git_${spindle}_1) &&
        echo -n 'Testing remote.origin.url ... ' &&
        git config remote.origin.url >config &&
        grep -q git@\$host config &&
        echo -n 'OK\nTesting remote.upstream.url ... ' &&
        (git config remote.upstream.url && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting remote.pushDefault ... ' &&
        git config remote.pushDefault >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-branch.remote ... ' &&
        git config branch.git-1-branch.remote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-branch.merge ... ' &&
        git config branch.git-1-branch.merge >config &&
        grep -q 'refs/heads/git-1-branch' config &&
        echo -n 'OK\nTesting branch.git-1-branch.pushRemote ... ' &&
        git config branch.git-1-branch.pushRemote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-2-branch.remote ... ' &&
        (git config branch.git-2-branch.remote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-2-branch.merge ... ' &&
        (git config branch.git-2-branch.merge && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-2-branch.pushRemote ... ' &&
        (git config branch.git-2-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.remote ... ' &&
        git config branch.git-1-and-2-branch.remote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.merge ... ' &&
        git config branch.git-1-and-2-branch.merge >config &&
        grep -q 'refs/heads/git-1-and-2-branch' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.pushRemote ... ' &&
        git config branch.git-1-and-2-branch.pushRemote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.local-branch.remote ... ' &&
        (git config branch.local-branch.remote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.local-branch.merge ... ' &&
        (git config branch.local-branch.merge && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.local-branch.pushRemote ... ' &&
        (git config branch.local-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo 'OK')
    "
done

for spindle in lab hub bb; do
    test_expect_success $spindle "Setting fork origin triangularly with non-existing fixed upstream branch to $spindle" "
        rm -rf whelk &&
        cp -a whelk-src whelk &&
        (cd whelk &&
        git_${spindle}_2 set-origin --triangular --upstream-branch non-existing-branch &&
        git remote -v &&
        host=$(spindle_host git_${spindle}_2) &&
        echo -n 'Testing remote.origin.url ... ' &&
        git config remote.origin.url >config &&
        grep -q git@\$host config &&
        echo -n 'OK\nTesting remote.upstream.url ... ' &&
        git config remote.upstream.url >config &&
        grep -q \"https://\\(.*@\\)\\?\$host\" config &&
        echo -n 'OK\nTesting remote.pushDefault ... ' &&
        git config remote.pushDefault >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-branch.remote ... ' &&
        git config branch.git-1-branch.remote >config &&
        grep -q 'upstream' config &&
        echo -n 'OK\nTesting branch.git-1-branch.merge ... ' &&
        git config branch.git-1-branch.merge >config &&
        grep -q 'refs/heads/git-1-branch' config &&
        echo -n 'OK\nTesting branch.git-1-branch.pushRemote ... ' &&
        (git config branch.git-1-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.git-2-branch.remote ... ' &&
        git config branch.git-2-branch.remote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-2-branch.merge ... ' &&
        git config branch.git-2-branch.merge >config &&
        grep -q 'refs/heads/git-2-branch' config &&
        echo -n 'OK\nTesting branch.git-2-branch.pushRemote ... ' &&
        git config branch.git-2-branch.pushRemote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.remote ... ' &&
        git config branch.git-1-and-2-branch.remote >config &&
        grep -q 'upstream' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.merge ... ' &&
        git config branch.git-1-and-2-branch.merge >config &&
        grep -q 'refs/heads/git-1-and-2-branch' config &&
        echo -n 'OK\nTesting branch.git-1-and-2-branch.pushRemote ... ' &&
        git config branch.git-1-and-2-branch.pushRemote >config &&
        grep -q 'origin' config &&
        echo -n 'OK\nTesting branch.local-branch.remote ... ' &&
        (git config branch.local-branch.remote && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.local-branch.merge ... ' &&
        (git config branch.local-branch.merge && (exit 2) || test \$? -eq 1) &&
        echo -n 'OK\nTesting branch.local-branch.pushRemote ... ' &&
        (git config branch.local-branch.pushRemote && (exit 2) || test \$? -eq 1) &&
        echo 'OK')
    "
done

for spindle in lab hub bb; do
    for protocol in ssh http git; do
        case $spindle-$protocol in
            lab-git)
                continue;;
            bb-git)
                continue;;
           *-ssh)
                scheme=git@;;
           *-http)
                scheme="https://\\(.*@\\)\\?";;
           *-git)
                scheme=git://;;
        esac
        test_expect_success $spindle "Setting origin to $spindle ($protocol)" "
            rm -rf whelk &&
            cp -a whelk-src whelk &&
            (cd whelk &&
            host=$(spindle_host git_${spindle}_2) &&
            git_${spindle}_2 set-origin --$protocol &&
            git remote -v &&
            git config remote.origin.url >config &&
            grep -q \"^$scheme\$host\" config &&
            git config remote.upstream.url >config &&
            grep -q \"^$scheme\$host\" config)
        "
    done
done

test_expect_success lab_local "Setting origin (local gitlab)" "
    rm -rf whelk &&
    cp -a whelk-src whelk &&
    (cd whelk &&
    host=$(spindle_host git_lab_local) &&
    git_lab_local set-origin &&
    git remote -v &&
    git config remote.origin.url >config &&
    grep -q \$host config)
"
test_done

# vim: set syntax=sh:
