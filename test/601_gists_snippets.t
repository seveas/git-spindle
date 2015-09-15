#!/bin/sh

test_description="Testing gists/snippets"

. ./setup.sh

cat <<EOF >test.txt
This is a gist/snippet test.
Hello, world!
EOF
cat <<EOF >test2.txt
This is a gist/snippet test.
Hello again, world!
EOF
cat <<EOF >stdin.txt
This is a gist/snippet stdin test.
Hello, world!
EOF

test_expect_success hub "Deleting existing gists (hub)" "
    (export DEBUG=1 &&
    git_hub_1 test-cleanup --gists)
"
test_expect_success hub "Creating a gist from a file (hub)" "
    rm -rf gist &&
    git_hub_1 gist test.txt > actual &&
    git clone \$(sed -e 's/.* //' actual) gist &&
    test_cmp test.txt gist/test.txt
"
test_expect_success hub "Creating a gist from multiple files (hub)" "
    rm -rf gist &&
    git_hub_1 gist test.txt test2.txt --description='Multiple files' > actual &&
    git clone \$(sed -e 's/.* //' actual) gist &&
    test_cmp test.txt gist/test.txt &&
    test_cmp test2.txt gist/test2.txt
"
test_expect_success hub "Creating a gist from stdin (hub)" "
    rm -rf gist &&
    cat stdin.txt | git_hub_1 gist - > actual &&
    git clone \$(sed -e 's/.* //' actual) gist &&
    test_cmp stdin.txt gist/stdout
"
test_expect_success hub "Listing gists (hub)" "
    git_hub_1 gists > actual &&
    test \$(wc -l <actual) = 3 &&
    grep -q 'Multiple files' actual
"

test_expect_success bb "Deleting existing snippets (bb)" "
    (export DEBUG=1 &&
    git_bb_1 test-cleanup --gists)
"
test_expect_success bb "Creating a snippet from a file (bb)" "
    rm -rf snippet &&
    git_bb_1 snippet test.txt > actual &&
    git clone \$(sed -e 's/.* //' actual) snippet &&
    test_cmp test.txt snippet/test.txt
"
test_expect_success bb "Creating a snippet from multiple files (bb)" "
    rm -rf snippet &&
    git_bb_1 snippet test.txt test2.txt --description='Multiple files' > actual &&
    git clone \$(sed -e 's/.* //' actual) snippet &&
    test_cmp test.txt snippet/test.txt &&
    test_cmp test2.txt snippet/test2.txt
"
test_expect_success bb "Creating a snippet from stdin (bb)" "
    rm -rf snippet &&
    cat stdin.txt | git_bb_1 snippet - > actual &&
    git clone \$(sed -e 's/.* //' actual) snippet &&
    test_cmp stdin.txt snippet/stdout
"
test_expect_success bb "Listing snippets (bb)" "
    git_bb_1 snippets > actual &&
    test \$(wc -l <actual) = 3 &&
    grep -q 'Multiple files' actual
"
test_done

# vim: set syntax=sh:
