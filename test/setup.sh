. ./sharness.sh

if [ ! -e "$SHARNESS_TEST_DIRECTORY/.gitspindle" ]; then
    echo "No .gitspindle found in test directory, aborting">&2
    exit 1
fi

cp "$SHARNESS_TEST_DIRECTORY/.gitspindle" .
export PYTHONPATH="$SHARNESS_BUILD_DIRECTORY/lib"
export GIT_CEILING_DIRECTORIES="$SHARNESS_BUILD_DIRECTORY"

if [ x"$PYTHON" = x ]; then
    PYTHON=python
fi

git_hub() { "$PYTHON" "$SHARNESS_BUILD_DIRECTORY/bin/git-hub" "$@"; }
git_lab() { "$PYTHON" "$SHARNESS_BUILD_DIRECTORY/bin/git-lab" "$@"; }
git_bb() { "$PYTHON" "$SHARNESS_BUILD_DIRECTORY/bin/git-bb" "$@"; }

# Make sure git doesn't think we're in a repo
git rev-parse >/dev/null 2>&1 && { echo "Yikes, git sees an outer repo!"; exit 1; }
