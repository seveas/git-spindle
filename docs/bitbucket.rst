Git spindle for BitBucket
=========================

:command:`git bucket` or :command:`git bb` lets you use your BitBucket account
from the command line.  Among other things, it lets you create and fork
repositories, or file pull requests.

Basic usage
-----------
The first time you use :command:`git bb`, it will ask you for your BitBucket
username and password. These are stored in :file:`~/.gitspindle`. Never share
this file with anyone as it gives full access to your BitBucket account.

.. describe:: git bb whoami

A simple command to try out is :command:`git bb whoami`, which tells you what
BitBucket thinks about who you are. For example::

  dennis@lightning:~$ git bb whoami
  Dennis Kaarsemaker
  [1;4mDennis Kaarsemaker[0m
  Profile:  https://bitbucket.org/seveas
  Website:  http://www.kaarsemaker.net/
  Location: The Netherlands
  RSA key   ...N0nFw3oW5l (Dennis Kaarsemaker (git))

.. describe:: git bb whois <user>...

If you want to see this information about other users, use :command:`git bb whois`::

  dennis@lightning:~$ git bb whois bblough
  [1;4mBill Blough[0m
  Profile:  https://bitbucket.org/bblough

.. describe:: git bb repos [--no-forks] [<user>]

List all repositories owned by a user, by default you. Specify :option:`--no-forks`
to exclude forked repositories.

.. describe:: git bb add-public-keys [<key>...]

Add SSH public keys (default: :file:`~/.ssh/*.pub`) to your account.

.. describe:: git bb public-keys [<user>]

Display all public keys of a user, in a format that can be added to
:file:`~/.authorized_keys`.

Using multiple accounts
-----------------------
:command:`git bb` supports using more than one account. To use a non-default,
you have to tell :command:`git bb` which account to use using
:option:`--account`::

    $ git bb --account test-account clone seveas/whelk

.. describe:: git bb add-account <alias>

To add a new account, use the :command:`add-account` command.

.. describe:: git bb config [--unset] <key> [<value>]

Set, get or unset a configuration variable in :file:`~/.gitspindle`. Similar to
:command:`git config`, but only single-level keys are allowed, and the section
is hardcoded to be the current account.

Interacting with repositories
-----------------------------

.. describe:: git bb create [--private] [--team=<team>] [--description=<description>]

Create a (possibly private) repository on BitBucket for your current repository. An
optional description can be given too. After running this command, a repository
will be created on BitBucket and your local repository will have BitBucket as remote
"origin", so :command:`git push origin master` will work.

By default the repository is created under your account, but you can specify a
team to create the repository for.

.. describe:: git bb set-origin [--ssh|--http] [--triangular [--upstream-branch=<branch>]]

Fix the configuration of your repository's remotes. The remote "origin" will be
set to your BitBucket repository. If "origin" is a fork, an "upstream" remote will
be set to the repository you forked from.

All non-tracking branches with a matching counterpart in "origin" will be set to
track "origin" (push and pull to it). Use :option:`--triangular` to set remotes
in a triangular fashion where :command:`git pull` pulls from "upstream" and
:command:`git push` pushes to "origin". This also sets the configuration option
:option:`remote.pushDefault`, so that new branches are pushed to "origin" even
if they track a branch in "upstream". All non-tracking branches are set up to
track a matching counterpart in "upstream" except if :option:`--upstream-branch`
explicitly specifies a branch like "master" in "upstream" that all branches should
track.

For "origin", an SSH url is used. For "upstream", set-origin defaults to adding
a git url, but this can be overridden. For private repos, SSH is used.

.. describe:: git bb clone [--ssh|--http] [--triangular [--upstream-branch=<branch>]] [--parent] [git-clone-options] <repo> [<dir>]

Clone a BitBucket repository by name (e.g. seveas/whelk) or URL. The "origin"
remote will be set and, like with set-origin, if "origin" is a fork the
"upstream" remote will be set too. The option :option:`--triangular` can be used
for a triangular setup.

Defaults to cloning from a git url, but this can be overridden. For private
repos, SSH is used.

This command accepts all options git clone accepts and will forward those to
:command:`git clone`.

.. describe:: git bb cat <file>...

Display the contents of a file on BitBucket. File can start with repository
names and refs. For example: `master:bin/git-bb`,
`git-spindle:master:bin/git-bb` or `seveas/git-spindle:master:bin/git-bb`.

.. describe:: git bb ls [<dir>...]

Display the contents of a directory on BitBucket. Directory can start with
repository names and refs. For example: `master:bin/git-bb`,
`git-spindle:master:bin/git-bb` or `seveas/git-spindle:master:bin/git-bb`.

.. describe:: git bb fork [--ssh|--http] [--triangular [--upstream-branch=<branch>]] [<repo>]

Fork another person's git repository on BitBucket and clone that repository
locally. The repository can be specified as a (git) url or simply username/repo.
Like with set-origin, the "origin" and "upstream" remotes will be set up too.
The option :option:`--triangular` can be used for a triangular setup.

Defaults to cloning from a git url, but this can be overridden.

Calling fork in a previously cloned-but-not-forked repository will create a
fork of that repository and set up your remotes.

.. describe:: git bb forks [<repo>]

List all forks of this repository, highlighting the original repository.

.. describe:: git bb add-remote [--ssh|--http] <user> [<name>]

Add a users fork as a remote using the specified name or the user's login as
name for the remote. Defaults to adding an http url, but this can be
overridden. For private repos SSH is used.

.. describe:: git bb fetch [--ssh|--http] <user> [<refspec>]

If you don't want to add a user's fork as a remote, but to want to fetch some
refs from it, you can use the :command:`fetch` command. You can tell it which
refs to fetch, and if you don't give a refspec, it will fetch all branches.

.. describe:: git bb browse [--parent] [<repo>] [<section>]

Browse a repository (or its parent) on BitBucket. By default the repository's
homepage is opened, but you can specify a different section, such as src,
src, commits, branches, pull-requests, downloads, admin, issues or wiki.

.. describe:: git bb mirror [--ssh|--http] [--goblet] [<repo>]

Mirror a repository from BitBucket. This is similar to clone, but clones into a
bare repository and maps all remote refs to local refs. When run without
argument, the current repository will be updated. You can also specify
:option:`user/*` as repository to mirror all repositories of a user.

When you use the :option:`--goblet` option, the resulting mirror will be
configured for the goblet web interface, using description, owner and clone
information from BitBucket.

Administering repositories
--------------------------
.. describe:: git bb privileges [<repo>]

List all people with access to this repository. Beware that BitBucket
aggressively caches permissions and it can take up to a minute for a change in
permissions to be reflected in the output of this command. The owner of the
repository is also not listed in the output.

.. describe:: git bb add-privilege [--admin|--read|--write] <user>...

Grant people read, write or admin access to this repository.

.. describe:: git bb remove-privilege <user>...

Revoke access to this repository.

.. describe:: git bb invite [--read|--write|--admin] <email>...

Invite users by e-mail to collaborate on this repository.

.. describe:: git bb deploy-keys [<repo>]

List all deploy keys for this repository

.. describe:: git bb add-deploy-key <key>...

Add a deploy key to a repository, which can be used to fetch and push data via
ssh.

.. describe:: git bb remove-deploy-key <key>...

Remove a deploy key by id. Use the :command:`git bb deploy-keys` command to
see the id's of your deploy keys.

Issues and pull requests
------------------------

.. describe:: git bb issues [<repo>] [--parent] [<filter>...]

List all open issues for the current repository, or the one specified in the
`<repo>` argument. If you run this outside a repository, or with `--` as
`<repo>`, it will list issues in all your repositories.  When you
specify :option:`--parent`, this will operate on the parent repositoryD.

You can specify filters in the form `filter=value` to filter issues. Supported
filters are:

 * status, accepted values: new, open, resolved, on hold, invalid, duplicate, wontfix
 * priority, accepted values; trivial, minor, major, critical, blocker
 * title
 * is_spam, accepted values: true, false

Filter values can be prefixed with ! to negate the match, ~, or ^ or $ to
indicate a 'contains', 'starts with' or 'ends with' operation.

.. describe:: git bb issue [<repo>] [--parent] [<issue>...]

Shows details about the mentioned issue numbers. As with :option:`issues`, you
can use the :option:`--parent` option to use the parent repository. If you do
not specify an issue number, you will be prompted for a message that will be
used to create a new issue.

.. describe:: git bb pull-request [--yes] [<yours:theirs>]

Files a pull request to merge branch "yours" (default: the current branch) into
the upstream branch "theirs" (default: the tracked branch of "yours" if it is in
the upstream repository, otherwise the default branch of the upstream
repository, usually "master"). Like for a commit message, your
editor will be opened to write a pull request message. The comments of said
message contain the shortlog and diffstat of the commits that you're asking to
be merged. Note that if you use any characterset in your logs and filenames
that is not ascii or utf-8, git bb will misbehave.

.. describe:: git bb apply-pr <pr-number>

BitBucket makes it easy for you to merge pull requests, but if you want to keep
your history linear, this one is for you. It applies a pull request using
:command:`git cherry-pick` instead of merging.

Snippets
--------

.. describe:: git bb snippet [--description=<description>] <file>...

Creates a snippet (with optional description) from the named files. If you specify
:file:`-` as filename, :file:`stdin` will be used, making it easy to pipe
command output to BitBucket, for example: :command:`fortune | git bb snippet -`

.. describe:: git bb snippets [<user>]

List your snippets, or those created by another user.
