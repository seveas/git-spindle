Git spindle for GitLab
======================
:command:`git lab` lets you use your GitLab instance from the command line.
Among other things, it lets you create and fork repositories, or file merge
requests.

Basic usage
-----------
The first time you use :command:`git lab`, it will ask you for your GitLab
username and password. It then requests (and stores) your API authentication.

The authentication token is stored in :file:`~/.gitspindle`. Never share this
token with anyone as it gives full access to your GitLab account.

.. describe:: git lab whoami

A simple command to try out is :command:`git lab whoami`, which tells you what
GitLab thinks about who you are. For example::

  dennis@lightning:~$ git lab whoami
  GitLab user: seveas
  GitLab password:
  [1;4mDennis Kaarsemaker (id 57597)[0m
  Profile   https://gitlab.com/u/seveas
  Email     dennis@kaarsemaker.net
  Website   http://www.kaarsemaker.net
  Twitter   seveas
  LinkedIn  http://nl.linkedin.com/in/denniskaarsemaker
  Bio       Python developer, linux admin, solving scalability issues at booking.com
  RSA key   ...N0nFw3oW5l (Dennis Kaarsemaker (git))

.. describe:: git lab whois <user>...

If you want to see some information about other users, use :command:`git lab whois`::

  dennis@lightning:~$ git lab whois sigmavirus24
  [1;4mIan Cordasco (id 6325)[0m
  Profile   https://gitlab.com/u/sigmavirus24

Sadly, GitLab does not give a lot of information about other users.

.. describe:: git lab repos [--no-forks]

List all your repositories. Specify :option:`--no-forks` to exclude forked
repositories.

.. describe:: git lab add-public-keys [<key>...]

Add SSH public keys (default: :file:`~/.ssh/*.pub`) to your account.

.. describe:: git lab public-keys [<user>]

Display all public keys of a user, in a format that can be added to
:file:`~/.authorized_keys`. Note that only admins can see this information for
other users.

.. describe:: git lab log [<repo>]

Displays a log of actions done to a repository, such as pushes and issue
comments.

Using multiple accounts
-----------------------
:command:`git lab` supports using more than one account, and using local
installs of GitLab CE and EE. To use a non-default account outside a
repository, for example when cloning, you have to tell :command:`git lab` which
account to use using :option:`--account`::

    $ git lab --account test-account clone seveas/whelk

If the account is on a Gitlab enterprise installation, you don't need to use
--account all the time. git-spindle will recognize the account from the url in
your repository configuration::

    $ git lab --account work clone dev/website
    $ cd website
    $ git lab issues

.. describe:: git lab add-account [--host=<host>] <alias>

To add a new account, use the :command:`add-account` command. If the account
lives on a GitLab EE or CE instance other than gitlab.com, you can specify its
hostname.

.. describe:: git lab config [--unset] <key> [<value>]

Set, get or unset a configuration variable in :file:`~/.gitspindle`. Similar to
:command:`git config`, but only single-level keys are allowed, and the section
is hardcoded to be the current account.

To change the hostname of any account, including the default one, you can use
the :command:`config` command as follows: :command:`git lab config host
https://gitlab.example.com`.

Interacting with repositories
-----------------------------

.. describe:: git lab create [--private|--internal] [--group=<group>] [--description=<description>]

Create a (possibly private/internal) repository on GitLab for your current
repository. An optional description can be given too. After running this
command, a repository will be created on GitLab and your local repository will
have GitLab as remote "origin", so :command:`git push origin master` will work.

By default the repository is created under your account, but you can specify a
group to create the repository for.

.. describe:: git lab set-origin [--ssh|--http] [--triangular [--upstream-branch=<branch>]]

Fix the configuration of your repository's remotes. The remote "origin" will be
set to your GitLab repository. If "origin" is a fork, an "upstream" remote will
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

.. describe:: git lab clone [--ssh|--http] [--triangular [--upstream-branch=<branch>]] [--parent] [git-clone-options] <repo> [<dir>]

Clone a GitLab repository by name (e.g. seveas/hacks) or URL. The "origin"
remote will be set and, like with set-origin, if "origin" is a fork t
"upstream" remote will be set too. The option :option:`--triangular` can be used
for a triangular setup.

Defaults to cloning from an http url, but this can be overridden. For private
repos, SSH is used.

This command accepts all options git clone accepts and will forward those to
:command:`git clone`.

.. describe:: git lab cat <file>...

Display the contents of a file on GitLab. File can start with repository names
and refs. For example: `master:bin/git-lab`, `git-spindle:master:bin/git-lab`
or `seveas/git-spindle:master:bin/git-lab`.

.. describe:: git lab ls [<dir>...]

Display the contents of a directory on GitLab. Directory can start with
repository names and refs. For example: `master:bin/git-lab`,
`git-spindle:master:bin/git-lab` or `seveas/git-spindle:master:bin/git-lab`.

.. describe:: git lab fork [--ssh|--http] [--triangular [--upstream-branch=<branch>]] [<repo>]

Fork another person's git repository on GitLab and clones that repository
locally. Repo can be specified as a (git) url or simply username/repo. Like with
set-origin, the "origin" and "upstream" remotes will be set up too. The option
:option:`--triangular` can be used for a triangular setup.

Defaults to cloning from a git url, but this can be overridden.

Calling fork in a previously cloned-but-not-forked repository will create a
fork of that repository and set up your remotes.

.. describe:: git lab add-remote [--ssh|--http] <user> [<name>]

Add a users fork as a remote using the specified name or the user's login as
name for the remote. Defaults to adding an http url, but this can be
overridden. For private repos SSH is used.

.. describe:: git lab fetch [--ssh|--http] <user> [<refspec>]

If you don't want to add a user's fork as a remote, but to want to fetch some
refs from it, you can use the :command:`fetch` command. You can tell it which
refs to fetch, and if you don't give a refspec, it will fetch all branches.

.. describe:: git lab browse [--parent] [<repo>] [<section>]

Browse a repository (or its parent) on GitLab. By default the repository's
homepage is opened, but you can specify a different section, such as issues,
merge_requests, wiki, files, commits, branches, graphs or settings.

.. describe:: git lab mirror [--ssh|--http] [--goblet] [<repo>]

Mirror a repository from GitLab. This is similar to clone, but clones into a
bare repository and maps all remote refs to local refs. When run without
argument, the current repository will be updated. You can also specify
:option:`*` as repository to mirror all your repositories.

When you use the :option:`--goblet` option, the resulting mirror will be
configured for the goblet web interface, using description, owner and clone
information from GitLab.

Administering repositories
--------------------------
.. describe:: git lab members [<repo>]

List all people with push access to this repository.

.. describe:: git lab add-member [--access-level=guest|reporter|developer|master|owner] <user>...

Grant people access to this repository.

.. describe:: git lab remove-member <user>...

Revoke access to this repository.

.. describe:: git lab protected

List all protected branches. Protected branches cannot be force-pushed or
deleted, and can only be pushed to by people with the master or owner access
level.

.. describe:: git lab protect <branch>

Mark a branch as protected.

.. describe:: git lab unprotect <branch>

Remove a branch's protection.

Issues and pull requests
------------------------

.. describe:: git lab issues [<repo>] [--parent] [<filter>...]

List all open issues for the current repository, or the one specified in the
`<repo>` argument. If you run this outside a repository, or with `--` as
`<repo>`, it will list issues in all your repositories.  When you
specify :option:`--parent`, this will operate on the parent repositoryD.

You can specify filters in the form `filter=value` to filter issues. Supported
filters are:

 * state, accepted values: opened, closed
 * labels, accepted values: comma-separated list of labels, e.g. bug,ui,@high
 * scope, accepted values: all, created-by-me, assigned-to-me
 * order_by, accepted values: created_at, updated_at
 * sort, accepted values: asc, desc

.. describe:: git lab issue [<repo>] [--parent] [<issue>...]

Shows details about the mentioned issue numbers. As with :option:`issues`, you
can use the :option:`--parent` option to use the parent repository. If you do
not specify an issue number, you will be prompted for a message that will be
used to create a new issue.

.. describe:: git lab merge-request [--yes] [<yours:theirs>]

Files a pull request to merge branch "yours" (default: the current branch) into
the upstream branch "theirs" (default: the tracked branch of "yours" if it is in
the upstream repository, otherwise the default branch of the upstream
repository, usually "master"). Like for a commit message, your
editor will be opened to write a pull request message. The comments of said
message contain the shortlog and diffstat of the commits that you're asking to
be merged. Note that if you use any characterset in your logs and filenames
that is not ascii or utf-8, git lab will misbehave.

If you specify an issue number, that issue will be turned into a pull request
and you will not be asked to write a pull request message.

.. describe:: git lab apply-merge <merge-request-number>

GitLab makes it easy for you to merge merge requests, but if you want to keep
your history linear, this one is for you. It applies a merge request using
:command:`git cherry-pick` instead of merging.

.. _`filters`: https://github.com/gitlabhq/gitlabhq/blob/master/doc/api/issues.md

Other
-----
.. describe:: git lab calendar [<user>]

Show a timeline of a your activity, or that of another user. The timeline will
look like that on your GitLab profile page.
