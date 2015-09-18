#!/bin/sh

test_description="Testing add_remote"

. ./setup.sh

test_expect_success "Clone source repository" "
    git_hub_1 clone whelk
"

for spindle in hub lab bb; do
    for proto in ssh http git; do
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
        test_expect_success $spindle "Adding a $spindle/$proto remote" "
            (cd whelk &&
            src=\$(username git_${spindle}_2) &&
            { git remote remove \$src 2>&1 || true; } &&
            git_${spindle}_1 add-remote --$proto \$src &&
            git remote -v &&
            git config remote.\$src.url | grep -q \"^$scheme\$host.*\$src\")
        "
    done
    test_expect_success $spindle "Adding a $spindle remote with a name" "
        (cd whelk &&
        src=\$(username git_${spindle}_2) &&
        { git remote remove \$src-x 2>&1 || true; } &&
        git_${spindle}_1 add-remote --http \$src \$src-x &&
        git remote -v &&
        git config remote.\$src-x.url | grep -q \"^https://\$host.*\$src/\")
    "
done

test_done

# vim: set syntax=sh:
