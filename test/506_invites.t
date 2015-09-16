#!/bin/sh

test_description="Testing bitbucket invites"

. ./setup.sh

email() {(
    export DEBUG=1
    $1 run-shell -c "print([x['email'] for x in self.me.emails() if x['primary']][0])"
)}

test_expect_success bb "Inviting users" "
    email_1=$(email git_bb_2) &&
    email_2=$(email git_bb_3) &&
    git_bb_1 clone whelk &&
    (cd whelk &&
    echo \"Invitation with read privileges sent to \$email_1\" > expected &&
    echo \"Invitation with write privileges sent to \$email_2\" >> expected &&
    git_bb_1 invite \$email_1 > actual &&
    git_bb_1 invite --write \$email_2 >> actual &&
    test_cmp expected actual)
"

test_done

# vim: set syntax=sh:
