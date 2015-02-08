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

.. describe:: git bb whois

If you want to see this information about other users, use :command:`git bb whois`::

  dennis@lightning:~$ git bb whois bblough
  [1;4mBill Blough[0m
  Profile:  https://bitbucket.org/bblough

.. describe:: git bb repos [--no-forks] [<user>...]

List all repositories owned by a user, by default you. Specify :option:`--no-forks`
to exclude forked repositories.

.. describe:: git bb add-public-keys [<key>...]

Add SSH public keys (default: :file:`~/.ssh/*.pub`) to your account.

.. describe:: git bb public-keys <user>

Display all public keys of a user, in a format that can be added to
:file:`~/.authorized_keys`.

Interacting with repositories
-----------------------------

.. describe:: git bb create [--private] [-d <description>]

Create a (possibly private) repository on BitBucket for your current repository. An
optional description can be given too. After running this command, a repository
will be created on BitBucket and your local repository will have BitBucket as remote
"origin", so :command:`git push origin master` will work.

.. describe:: git bb set-origin [--ssh|--http]

Fix the configuration of your repository's remotes. Remote "origin" will be set
to your BitBucket repository. If that repository is a fork, remote "upstream" will
be set to the repository you forked from.

For origin, an SSH url is used. For upstream, set-origin defaults to adding an
http url, but this can be overridden. For private repos SSH is used.

.. describe:: git bb clone [--ssh|--http] [--parent] [git-clone-options] <repo> [<dir>]

Clone a BitBucket repository by name (e.g. seveas/whelk) or URL. If it's a fork,
the "upstream" origin will be set up too. Defaults to cloning from an http url,
but this can be overridden. For private repos SSH is used.

This command accepts all options git clone accepts and will forward those to
:command:`git clone`.

.. describe:: git bb fork [--ssh|--http] [<repo>]

Fork another person's git repository on BitBucket and clone that repository
locally. Repo can be specified as a (git) url or simply username/repo. Like
with set-origin, the "origin" and "upstream" remotes will be set up too.

Calling fork in a previously cloned-but-not-forked repository will create a
fork of that repository and set up your remotes.

.. describe:: git bb forks

List all forks of this repository, highlighting the original repository.

.. describe:: git bb add-remote [--ssh|--http] [<user>]

Add a users fork as a remote using the user's login as name for the remote.
Defaults to adding an http url, but this can be overridden. For private repos
SSH is used.

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

Issues and pull requests
------------------------

.. describe:: git bb issues [<repo>] [--parent] [<filter>...]

List all open issues. You can specify filters to filter issues. When you
specify :option:`--parent`, list all open issues for the parent repository.

.. describe:: git bb issue [<repo>] [--parent] [<issue>...]

Shows details about the mentioned issue numbers. As with :option:`issues`, you
can use the :option:`--parent` option to use the parent repository. If you do
not specify an issue number, you will be prompted for a message that will be
used to create a new issue.

.. describe:: git bb pull-request <yours:theirs>

Files a pull request to merge branch "yours" (default: the current branch) into
the upstream branch "theirs" (default: master). Like for a commit message, your
editor will be opened to write a pull request message. The comments of said
message contain the shortlog and diffstat of the commits that you're asking to
be merged. Note that if you use any characterset in your logs and filenames
that is not ascii or utf-8, git bb will misbehave.

.. describe:: git bb apply-pr <pr-number>

BitBucket makes it easy for you to merge pull requests, but if you want to keep
your history linear, this one is for you. It applies a pull request using
:command:`git cherry-pick` instead of merging.
