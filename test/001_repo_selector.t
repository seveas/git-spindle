#!/bin/sh

test_description="Test repository selection"

. ./setup.sh

# Note that this test uses existing repositories on various services. Should
# they disappear, the tests will need to be updated. This is the very first
# test ran as this tests critical functionality to safely test other functions.
# Do not try to create repos here to test repo selection with.

# Needed to make run-shell work
export DEBUG=1

test_expect_success "Test prep" "
    git init &&
    git remote add origin http://github.com/seveas/whelk &&
    git remote add github http://github.com/reinout/whelk &&
    git remote add bitbucket http://bitbucket.org/seveas/whelk &&
    git remote add gitlab http://gitlab.com/seveas/whelk &&
    git remote add local http://gitlab.kaarsemaker.net/seveas2/whelk
"
 
test_expect_success "Selecting the right repo from the config" "
    echo '<Repository [seveas/whelk]>' > expected &&
    echo 'seveas/whelk' >> expected &&
    echo 'seveas/whelk' >> expected &&

    git_hub run-shell -c repo > actual &&
    git_lab run-shell -c \"print('%s/%s' % (repo.owner.username, repo.name))\" >> actual &&
    git_bb run-shell -c \"print('%s/%s' % (repo.owner['username'], repo.name))\" >> actual &&

    test_cmp expected actual
"

test_expect_success "Specifying a repo on the command line" "
    echo '<Repository [seveas/python-hpilo]>' > expected &&
    echo seveas/python-hpilo >> expected &&
    echo seveas/python-hpilo >> expected &&

    git_hub run-shell -c \"self.repository({'<repo>': 'seveas/python-hpilo', '--parent': False, '--maybe-parent': False})\" > actual &&
    git_lab run-shell -c \"r = self.repository({'<repo>': 'seveas/python-hpilo', '--parent': False, '--maybe-parent': False}); print('%s/%s' % (r.owner.username, r.name))\" >> actual &&
    git_bb run-shell -c \"r = self.repository({'<repo>': 'seveas/python-hpilo', '--parent': False, '--maybe-parent': False}); print('%s/%s' % (r.owner['username'], r.name))\" >> actual &&

    test_cmp expected actual
"

test_expect_success "Repository not found" "
    git remote set-url origin http://github.com/seveas/whelk.broken &&
    git remote set-url gitlab http://gitlab.com/seveas/whelk.broken &&
    git remote set-url bitbucket http://bitbucket.org/seveas/whelk.broken &&
    git remote rm local &&

    echo 'Repository seveas/whelk.broken could not be found on GitHub' > expected &&
    echo 'Repository seveas/whelk.broken could not be found on GitLab' >> expected &&
    echo 'Repository seveas/whelk.broken could not be found on BitBucket' >> expected &&

    test_must_fail git_hub run-shell -c repo 2> actual &&
    test_must_fail git_lab run-shell -c repo 2>> actual &&
    test_must_fail git_bb run-shell -c repo 2>> actual &&

    test_cmp expected actual
"

test_expect_success "GitLab local install" "
    git remote add local http://gitlab.kaarsemaker.net/seveas2/whelk &&

    echo seveas2/whelk > expected &&
    echo seveas2/whelk >> expected &&

    git_lab --account gitlab-test-local run-shell -c \"print('%s/%s' % (repo.owner.username, repo.name))\" > actual &&
    git remote rm gitlab &&
    git_lab run-shell -c \"print('%s/%s' % (repo.owner.username, repo.name))\" >> actual &&

    test_cmp expected actual
"

test_expect_success "Test outside repo" "
    rm -rf .git &&
    echo None > expected &&
    echo None >> expected &&
    echo None >> expected &&

    echo 'fatal: Not a git repository (or any of the parent directories): .git' >> expected &&
    echo 'fatal: Not a git repository (or any of the parent directories): .git' >> expected &&
    echo 'fatal: Not a git repository (or any of the parent directories): .git' >> expected &&

    git_hub run-shell -c 'print(repo)' > actual &&
    git_lab run-shell -c 'print(repo)' >> actual &&
    git_bb run-shell -c 'print(repo)' >> actual &&

    test_must_fail git_hub run-shell -c \"self.repository({'<repo>': None})\" 2>> actual &&
    test_must_fail git_lab run-shell -c \"self.repository({'<repo>': None})\" 2>> actual &&
    test_must_fail git_bb run-shell -c \"self.repository({'<repo>': None})\" 2>> actual &&

    test_cmp expected actual
"

test_expect_failure "Test fake GHE by pointing another name to GitHub" "false"
test_expect_failure "Test BitBucket CNAMEs" "false"

test_done

# vim: set syntax=sh:
