Using multiple accounts
=======================

:command:`git hub`, :command:`git bb` and :command:`git lab` all support using
more than one account. :command:`git hub` and :command:`git lab` also support
using local installs of GitHub Enterprise and GitLab.

Adding an extra account
-----------------------
To add an extra account, use the :command:`git hub add-account` command
(replace hub with lab or bb as appropriate in this and following commands). It
requires an alias as argument; this alias does not need to be the same as the
account name, which it will ask for later. This alias can be used in later
commands to specify which account to use.

Examples::

    $ git hub add-account personal
    GitHub user: seveas
    GitHub password: 
    A GitHub authentication token is now cached in ~/.gitspindle - do not share this file

    $ git lab add-account work --host gitlab.example.com
    GitLab user: seveas
    GitLab password:
    Your GitLab authentication token is now cached in ~/.gitspindle - do not share this file

As you can see you can use the same username on multiple services.

Using non-default accounts
--------------------------
To use these extra accounts, you can give :command:`git hub` an
:option:`--account` argument::

    $ git hub --account test-account clone seveas/whelk

Note that the value of this parameter should be an alias as used with the
:command:`add-account` command, not a loginname. If the account is on a
separate hostname, such as a GitHub Enterprise or local GitLab install, you do
not need to specify an account, except when cloning: git-spindle will recognize
it based on the configured remote url's::

    $ git lab --account work clone dev/website
    $ cd website
    $ git lab issues
