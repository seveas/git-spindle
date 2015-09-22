#!/bin/sh

test_description="Testing the use of credential helpers for token/password settings"

. ./setup.sh

export DEBUG=1

for spindle in hub lab bb; do
    spindle_dash="$(spindle_remote git_${spindle}_2)-test-2"
    tokenkey=token
    if [ $spindle = bb ]; then tokenkey=password; fi

    test_expect_success $spindle "Copying the secrets to the credential helper ($spindle)" "
        token=\$(git_${spindle}_2 config $tokenkey) &&
        git config --global credential.helper store &&
        test_when_finished 'git config --global --unset credential.helper' &&
        echo '' > expected &&
        git_${spindle}_2 config $tokenkey > actual &&
        test_cmp expected actual &&
        git_${spindle}_2 config $tokenkey \$token &&
        git_${spindle}_2 whoami | grep -q '^Profile.*/$(username git_${spindle}_2)'
    "

    test_expect_success $spindle "Authentication handler stores token/password correctly ($spindle)" "
        password=\$(git config -f .gitspindle testsuite.${spindle_dash}.password) &&
        test -n \"\$password\" &&
        git_${spindle}_2 config --unset token || test \$? -eq 5 &&
        git_${spindle}_2 config --unset password || test \$? -eq 5 &&
        git config --global credential.helper store &&
        git_${spindle}_2 config --unset token &&
        git_${spindle}_2 config --unset password &&
        echo \"\$password\" | git_${spindle}_2 whoami > actual &&
        grep $(username git_${spindle}_2) actual
    "

    test_expect_success $spindle "Copying new tokens back to the config ($spindle)" "
        token=\$(git_${spindle}_2 config $tokenkey) &&
        git config --global --unset credential.helper &&
        git_${spindle}_2 config $tokenkey \$token &&
        git_${spindle}_2 whoami | grep -q '^Profile.*/$(username git_${spindle}_2)'
    "
done 

# Make sure other tests know about the new tokens
test_expect_success "Updating global .gitspindle" "
    mv .gitspindle ..
"

test_done

# vim: set syntax=sh:
