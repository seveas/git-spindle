#!/bin/sh

test_description="Testing docstring propagation"

. ./setup.sh

test_expect_success author "Is README up-to-date" "
    for command in \$(git_hub -h | awk '
        /Options:/ { command = 0 }
        command { print \$1 }
        /Commands:/ { command = 1 }
    '); do git_hub -h \$command; echo; done > expected.tmp &&
    for command in \$(git_lab -h | awk '
        /Options:/ { command = 0 }
        command { print \$1 }
        /Commands:/ { command = 1 }
    '); do git_lab -h \$command; echo; done >> expected.tmp &&
    for command in \$(git_bb -h | awk '
        /Options:/ { command = 0 }
        command { print \$1 }
        /Commands:/ { command = 1 }
    '); do git_bb -h \$command; echo; done >> expected.tmp &&
    sed 's/ \\[options\\]//' expected.tmp > expected &&
    grep -C1 '^  git \\(hub\\|lab\\|bb\\) ' '$SHARNESS_BUILD_DIRECTORY/README' | grep -v '^--$' > actual &&
    test_cmp expected actual
"

test_expect_success author "Are usage strings in docs/ up-to-date" "
    grep '^  git \\(hub\\|lab\\|bb\\) ' expected.tmp | sed -s 's/ \\[options\\]//' > expected &&
    sed -ne 's/^\\.\\. describe::/ /p' '$SHARNESS_BUILD_DIRECTORY/docs/github.rst' | sort > actual &&
    sed -ne 's/^\\.\\. describe::/ /p' '$SHARNESS_BUILD_DIRECTORY/docs/gitlab.rst' | sort >> actual &&
    sed -ne 's/^\\.\\. describe::/ /p' '$SHARNESS_BUILD_DIRECTORY/docs/bitbucket.rst' | sort >> actual &&
    test_cmp expected actual
"

test_done

# vim: set syntax=sh:
