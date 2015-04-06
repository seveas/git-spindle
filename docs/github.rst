Git spindle for GitHub
======================

:command:`git hub` lets you use your GitHub account from the command line.
Among other things, it lets you create and fork repositories, or file pull
requests.

Basic usage
-----------
The first time you use :command:`git hub`, it will ask you for your GitHub
username and password. It then requests (and stores) an API authentication
token, so you can always revoke access from your `profile page`_.

The authentication token is stored in :file:`~/.gitspindle`. Never share this
token with anyone as it gives full access to your GitHub account.

.. describe:: git hub whoami

A simple command to try out is :command:`git hub whoami`, which tells you what
GitHub thinks about who you are. For example::

  dennis@lightning:~$ git hub whoami
  GitHub user: seveas
  GitHub password:
  [1;4mDennis Kaarsemaker[0m
  Profile   https://github.com/seveas
  Email     dennis@kaarsemaker.net
  Blog      http://www.kaarsemaker.net
  Location  Amsterdam
  Company   Booking.com
  Repos     36 public, 0 private
  Gists     4 public, 0 private
  RSA key   ...N0nFw3oW5l (Dennis)

.. describe:: git hub whois

If you want to see this information about other users, use :command:`git hub whois`::

  dennis@lightning:~$ git hub whois sigmavirus24
  [1;4mIan Cordasco[0m
  Profile   https://github.com/sigmavirus24
  Email     graffatcolmingov@gmail.com
  Blog      http://www.coglib.com/~icordasc/blog
  Repos     21 public, 0 private
  Gists     9 public, 0 private

.. describe:: git hub status

Shows the last few GitHub status messages::

  dennis@lightning:~$ git hub status
  [2m2014-04-01 23:06[0m [33mminor[0m Pages builds are paused while we investigate an increase in failed builds
  [2m2014-04-01 23:22[0m [32mgood [0m Everything operating normally.
  [2m2014-04-02 00:05[0m [33mminor[0m We're investigating reports of git operation failures.
  [2m2014-04-02 00:29[0m [31mmajor[0m We're experiencing problems with repo operations and are working to restore functionality.
  [2m2014-04-02 01:00[0m [31mmajor[0m Git and HTTPS repo operations are intermittently unavailable while we repair the source of the problem.
  [2m2014-04-02 01:22[0m [31mmajor[0m SSH git operations have been restored and we're working to fix HTTPS functionality.
  [2m2014-04-02 01:40[0m [33mminor[0m We have implemented a fix for the issue and git operations are recovering.
  [2m2014-04-02 01:47[0m [32mgood [0m Everything operating normally.
  [2m2014-04-03 09:55[0m [33mminor[0m We're currently investigating issues with operations against a small percentage of repositories.
  [2m2014-04-03 10:14[0m [32mgood [0m Everything operating normally.

.. describe:: git hub repos [--no-forks] [<user>...]

List all repositories owned by a user, by default you. Specify :option:`--no-forks`
to exclude forked repositories.

.. describe:: git hub add-public-keys [<key>...]

Add SSH public keys (default: :file:`~/.ssh/*.pub`) to your account.

.. describe:: git hub public-keys [<user>]

Display all public keys of a user, in a format that can be added to
:file:`~/.authorized_keys`.

.. describe:: git hub log [--type=<type>] [<what>]

Displays a log of your GitHub actions, such as pushes and issue comments. You
can also specify a user or repository and the relevant log will be shown
instead of yours.

If you are only interested in events of a specific type, you can filter for it,
e.g. :option:`--type=push`.

.. describe:: git hub config [--unset] <key> [<value>]

Set, get or unset a configuration variable in :file:`~/.gitspindle`. Similar to
:command:`git config`, but only single-level keys are allowed, and the section
is hardcoded to be the current account.

.. _`profile page`: https://github.com/settings/applications


Interacting with repositories
-----------------------------

.. describe:: git hub create [--private] [-d <description>]

Create a (possibly private) repository on GitHub for your current repository. An
optional description can be given too. After running this command, a repository
will be created on GitHub and your local repository will have GitHub as remote
"origin", so :command:`git push origin master` will work.

.. describe:: git hub set-origin [--ssh|--http|--git]

Fix the configuration of your repository's remotes. Remote "origin" will be set
to your GitHub repository. If that repository is a fork, remote "upstream" will
be set to the repository you forked from.

For origin, an SSH url is used. For upstream, set-origin defaults to adding a
git url, but this can be overridden. For private repos SSH is used.

.. describe:: git hub clone [--ssh|--http|--git] [--parent] [git-clone-options] <repo> [<dir>]

Clone a GitHub repository by name (e.g. seveas/hacks) or URL. If it's a fork,
the "upstream" origin will be set up too. Defaults to cloning from a git url,
but this can be overridden. For private repos SSH is used.

This command accepts all options git clone accepts and will forward those to
:command:`git clone`.

.. describe:: git hub cat <file>...

Display the contents of a file on GitHub. File can start with repository names
and refs. For example: `master:bin/git-hub`, `git-spindle:master:bin/git-hub`
or `seveas/git-spindle:master:bin/git-hub`.

.. describe:: git hub ls <dir>...

Display the contents of a directory on GitHub. Directory can start with
repository names and refs. For example: `master:bin/git-hub`,
`git-spindle:master:bin/git-hub` or `seveas/git-spindle:master:bin/git-hub`.

.. describe:: git hub fork [--ssh|--http|--git] [<repo>]

Fork another person's git repository on GitHub and clone that repository
locally. Repo can be specified as a (git) url or simply username/repo. Like
with set-origin, the "origin" and "upstream" remotes will be set up too.

Calling fork in a previously cloned-but-not-forked repository will create a
fork of that repository and set up your remotes.

.. describe:: git hub forks [<repo>]

List all forks of this repository, highlighting the original repository.

.. describe:: git hub add-remote [--ssh|--http|--git] [<user>]

Add a users fork as a remote using the user's login as name for the remote.
Defaults to adding a git url, but this can be overridden. For private repos
SSH is used.

.. describe:: git hub browse [--parent] [<repo>] [<section>]

Browse a repository (or its parent) on GitHub. By default the repository's
homepage is opened, but you can specify a different section, such as issues,
pulls, wiki, branches, releases, contributors, graphs, releases or settings.

.. describe:: git hub mirror [--ssh|--http|--git] [--goblet] [<repo>]

Mirror a repository from GitHub. This is similar to clone, but clones into a
bare repository and maps all remote refs to local refs. When run without
argument, the current repository will be updated. You can also specify
:option:`user/*` as repository to mirror all repositories of a user.

When you use the :option:`--goblet` option, the resulting mirror will be
configured for the goblet web interface, using description, owner and clone
information from GitHub.

.. describe:: git hub hooks

Show all service hooks for this repository.

.. describe:: git hub add-hook <name> [<setting>...]

Add a hook to this repository with the appropriate settings. Settings can be
found in the hooks page on GitHub. One setting all hooks accept is
:data:`events`, a comma-separated list of events this hook will be triggered
for. A list of all events can be found on the `GitHub API page`_

.. describe:: git hub edit-hook <name> [<setting>...]

Edit one or more settings for a hook.

.. describe:: git hub remove-hook <name>

Remove a service hook.

.. _`GitHub API page`: http://developer.github.com/v3/repos/hooks/

Issues and pull requests
------------------------

.. describe:: git hub issues [<repo>] [--parent] [<filter>...]

List all open issues. You can specify `filters`_ to filter issues. When you
specify :option:`--parent`, list all open issues for the parent repository.

.. describe:: git hub issue [<repo>] [--parent] [<issue>...]

Shows details about the mentioned issue numbers. As with :option:`issues`, you
can use the :option:`--parent` option to use the parent repository. If you do
not specify an issue number, you will be prompted for a message that will be
used to create a new issue.

.. describe:: git hub pull-request [--issue <issue>] [<yours:theirs>]

Files a pull request to merge branch "yours" (default: the current branch) into
the upstream branch "theirs" (default: master). Like for a commit message, your
editor will be opened to write a pull request message. The comments of said
message contain the shortlog and diffstat of the commits that you're asking to
be merged. Note that if you use any characterset in your logs and filenames
that is not ascii or utf-8, git hub will misbehave.

If you specify an issue number, that issue will be turned into a pull request
and you will not be asked to write a pull request message.

.. describe:: git hub apply-pr <pr-number>

GitHub makes it easy for you to merge pull requests, but if you want to keep
your history linear, this one is for you. It applies a pull request using
:command:`git cherry-pick` instead of merging.

.. _`filters`: http://github3py.readthedocs.org/en/latest/repos.html#github3.repos.Repository.list_issues

Gists
-----

.. describe:: git hub gist [-d <description>] <file>...

Creates a gist (with optional description) from the named files. If you specify
:file:`-` as filename, :file:`stdin` will be used, making it easy to pipe
command output to GitHub, for example: :command:`fortune | git hub gist -`

.. describe:: git hub gists [<user>]

List your gists, or those created by another user.

Other
-----
.. describe:: git hub calendar [<user>...]

Show a timeline of a your activity, or that of another user. The timeline will
look like that on your GitHub profile page::

    Sep Oct     Nov     Dec       Jan     Feb     Mar       Apr     May     Jun       Jul     Aug     Sep
      [8m■ [0m[38;5;65m■ [0m[38;5;65m■ [0m[38;5;65m■ [0m[38;5;28m■ [0m[38;5;22m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;64m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;65m■ [0m[38;5;28m■ [0m[38;5;64m■ [0m[38;5;28m■ [0m[38;5;64m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;64m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m
  M   [8m■ [0m[38;5;22m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;28m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;28m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;64m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;22m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m
      [8m■ [0m[38;5;22m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;64m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m
  W   [8m■ [0m[38;5;65m■ [0m[38;5;65m■ [0m[38;5;65m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;28m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;64m■ [0m[38;5;65m■ [0m[38;5;64m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;28m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;64m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m
    [38;5;65m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;64m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;64m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;64m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m
  F [38;5;237m■ [0m[38;5;28m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;64m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m
    [38;5;65m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;64m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;64m■ [0m[38;5;65m■ [0m[38;5;64m■ [0m[38;5;65m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;65m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;237m■ [0m[38;5;65m■ [0m[38;5;237m■ [0m

.. describe:: git hub render [--save=<outfile>] <file>

Lets GitHub render a markdown page and displays the result in your browser or
save it to a file.

.. describe:: git hub ignore [<language>...]

GitHub provides :file:`.gitignore` templates for various languages and
environments. This command will let you quickly grab them and add them to your
:file:`.gitignore`. For example: :command:`git hub ignore Python C`

.. describe:: git hub network [<level>]

Generates a graphviz graph of people following you, people you follow or people
who's repositories you've forked. For example::

  git hub network | dot -T png -Grankdir=LR > network.png

Here's mine:

.. image:: _static/network.png
