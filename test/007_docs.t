#!/bin/sh

test_description="Testing docstring propagation"

. ./setup.sh

test_expect_success "Is README up-to-date" "
    git_hub_1 -h > expected.tmp &&
    git_lab_1 -h >> expected.tmp &&
    git_bb_1 -h >> expected.tmp &&
    grep '^  git \\(hub\\|lab\\|bb\\) ' expected.tmp | sed -s 's/ \\[options\\]//' > expected &&
    grep '^  git \\(hub\\|lab\\|bb\\) ' '$SHARNESS_BUILD_DIRECTORY/README' > actual &&
    test_cmp expected actual
"
test_expect_success "Are usage strings in docs/ up-to-date" "
    sed -ne 's/^\\.\\. describe::/ /p' '$SHARNESS_BUILD_DIRECTORY/docs/github.rst' | sort > actual &&
    sed -ne 's/^\\.\\. describe::/ /p' '$SHARNESS_BUILD_DIRECTORY/docs/gitlab.rst' | sort >> actual &&
    sed -ne 's/^\\.\\. describe::/ /p' '$SHARNESS_BUILD_DIRECTORY/docs/bitbucket.rst' | sort >> actual &&
    test_cmp expected actual
"

test_done

# vim: set syntax=sh:
