. ./sharness.sh

# Clear/set environment
unset SSH_AUTH_SOCK
export PYTHONPATH="$SHARNESS_BUILD_DIRECTORY/lib"
export PYTHONIOENCODING='UTF-8'
export PATH="$SHARNESS_TEST_DIRECTORY/bin:$PATH"
export GIT_CEILING_DIRECTORIES="$SHARNESS_BUILD_DIRECTORY"
export GIT_SSH="$SHARNESS_TEST_DIRECTORY/bin/ssh"

if [ x"$PYTHON" = x ]; then
    PYTHON=python
fi

# Make sure git doesn't think we're in a repo
git rev-parse >/dev/null 2>&1 && { echo "Yikes, git sees an outer repo!"; exit 1; }

# Copy config files
if [ ! -e "$SHARNESS_TEST_DIRECTORY/.gitspindle" ]; then
    echo "No .gitspindle found in test directory, aborting">&2
    exit 1
fi
cp "$SHARNESS_TEST_DIRECTORY/.gitspindle" .

# Support functions
git_hub() { "$PYTHON" "$SHARNESS_BUILD_DIRECTORY/bin/git-hub" "$@"; }
git_lab() { "$PYTHON" "$SHARNESS_BUILD_DIRECTORY/bin/git-lab" "$@"; }
git_bb()  { "$PYTHON" "$SHARNESS_BUILD_DIRECTORY/bin/git-bb"  "$@"; }

git_1() { GITSPINDLE_ACCOUNT="test-1" git "$@"; }
git_hub_1() { "$PYTHON" "$SHARNESS_BUILD_DIRECTORY/bin/git-hub" --account github-test-1    "$@"; }
git_lab_1() { "$PYTHON" "$SHARNESS_BUILD_DIRECTORY/bin/git-lab" --account gitlab-test-1    "$@"; }
git_bb_1()  { "$PYTHON" "$SHARNESS_BUILD_DIRECTORY/bin/git-bb"  --account bitbucket-test-1 "$@"; }

git_2() { GITSPINDLE_ACCOUNT="test-2" git "$@"; }
git_hub_2() { "$PYTHON" "$SHARNESS_BUILD_DIRECTORY/bin/git-hub" --account github-test-2    "$@"; }
git_lab_2() { "$PYTHON" "$SHARNESS_BUILD_DIRECTORY/bin/git-lab" --account gitlab-test-2    "$@"; }
git_bb_2()  { "$PYTHON" "$SHARNESS_BUILD_DIRECTORY/bin/git-bb"  --account bitbucket-test-2 "$@"; }

git_3() { GITSPINDLE_ACCOUNT="test-3" git "$@"; }
git_hub_3() { "$PYTHON" "$SHARNESS_BUILD_DIRECTORY/bin/git-hub" --account github-test-3    "$@"; }
git_lab_3() { "$PYTHON" "$SHARNESS_BUILD_DIRECTORY/bin/git-lab" --account gitlab-test-3    "$@"; }
git_bb_3()  { "$PYTHON" "$SHARNESS_BUILD_DIRECTORY/bin/git-bb"  --account bitbucket-test-3 "$@"; }

git_lab_local() { "$PYTHON" "$SHARNESS_BUILD_DIRECTORY/bin/git-lab" --account gitlab-test-local "$@"; }

all_spindles="git_hub_1 git_lab_1 git_bb_1 git_lab_local git_hub_2 git_lab_2 git_bb_2 git_hub_3 git_lab_3 git_bb_3"

test_commit() {
    fortune >testfile &&
    git add testfile &&
    git commit -m "Test commit"
}
