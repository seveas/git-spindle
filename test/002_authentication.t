#!/bin/sh

test_description="Test authentication"

. ./setup.sh

export DEBUG=1

for spindle in $all_spindles; do
    spindle_dash="$(spindle_remote $spindle)-test-$(echo $spindle | sed -e 's/.*_//')"
    spindle_root=$(echo $spindle | sed -e 's/_[^_]*$//')
    test_expect_success $(req $spindle) "Cleaning up $spindle authentication details" "
        $spindle config keepme 'empty section workaround' &&
        $spindle config --unset token || test \$? -eq 5 &&
        $spindle config --unset password || test \$? -eq 5 &&
        $spindle config --unset host || test \$? -eq 5 &&
        $spindle config --unset user || test \$? -eq 5
    "
    test_expect_success $(req $spindle) "Logging in $spindle" "
        user=\$(git config -f .gitspindle testsuite.${spindle_dash}.user) &&
        password=\$(git config -f .gitspindle testsuite.${spindle_dash}.password) &&
        host=\$(git config -f .gitspindle testsuite.${spindle_dash}.host || true) &&
        test -n \"\$user\" &&
        test -n \"\$password\" &&
        { test -z \"\$host\" || host=\"--host \$host\"; } &&
        if [ $spindle = git_hub_3 ]; then
            echo \"\$ $spindle_root add-account $spindle_dash \$host\"
            $spindle_root add-account $spindle_dash \$host
        else
            (echo \"\$user\"; echo \"\$password\" ) | $spindle_root add-account $spindle_dash \$host
        fi &&
        $spindle config --unset keepme
    "
done

test_expect_success "Resetting non-numbered accounts" "
    git_hub config user \$(git_hub_1 config user) &&
    git_hub config token \$(git_hub_1 config token) &&
    git_lab config user \$(git_lab_1 config user) &&
    git_lab config token \$(git_lab_1 config token) &&
    git_bb config user \$(git_bb_1 config user) &&
    git_bb config password \$(git_bb_1 config password)
"

# Make sure other tests know about the new tokens
test_expect_success "Updating global .gitspindle" "
    mv .gitspindle ..
"

test_done

# vim: set syntax=sh:
