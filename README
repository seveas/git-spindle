Integrating git with central services
=====================================

Many central git hosting services, such as GitHub and GitLab, provide an API to
perform actions such as creating repositories and filing pull requests.
git-spindle is a collection of git subcommands to make using these services
easier.

For example, to fork and clone a repository on GitHub, one can now simply use

    git hub clone seveas/whelk

With this git subcommand, you can perform various github actions, such as
creating or forking a repository from the command line.

To install the latest released version on Ubuntu:

    sudo add-apt-repository ppa:dennis/python
    sudo add-apt-repository ppa:dennis/devtools
    sudo apt-get update
    sudo apt-get install git-spindle

To install the latest released version on Windows:

    Install git from http://git-for-windows.github.io/
    Install python 3.5 or newer from https://www.python.org/downloads/
    Run the following 2 commands in a command prompt:
    py -mensurepip
    py -mpip install git-spindle

To install the latest released version on other systems, assuming python and
pip are installed:

    pip install git-spindle

Usage:

(For detailed information, go to http://seveas.github.com/git-spindle)

Add an account to the configuration:
  git hub add-account [--host=<host>] <alias>
Add a user as collaborator:
  git hub add-collaborator <user>...
Add a deploy key:
  git hub add-deploy-key [--read-only] <key>...
Add a repository hook:
  git hub add-hook <name> [<setting>...]
Adds keys to your public keys:
  git hub add-public-keys [<key>...]
Add user's fork as a named remote. The name defaults to the user's loginname:
  git hub add-remote [--ssh|--http|--git] <user> [<name>]
Applies a pull request as a series of cherry-picks:
  git hub apply-pr <pr-number>
Open the GitHub page for a repository in a browser:
  git hub browse [--parent] [<repo>] [<section>]
Show a timeline of a user's activity:
  git hub calendar [<user>]
Display the contents of a file on GitHub:
  git hub cat <file>...
Check the github pages configuration and content of your repo:
  git hub check-pages [<repo>] [--parent]
Clone a repository by name:
  git hub clone [--ssh|--http|--git] [--triangular [--upstream-branch=<branch>]] [--parent] [git-clone-options] <repo> [<dir>]
List collaborators of a repository:
  git hub collaborators [<repo>]
Configure git-spindle, similar to git-config:
  git hub config [--unset] <key> [<value>]
Create a repository on github to push to:
  git hub create [--private] [--org=<org>] [--description=<description>]
Create a personal access token that can be used for git operations:
  git hub create-token [--store]
Lists all keys for a repo:
  git hub deploy-keys [<repo>]
Edit a hook:
  git hub edit-hook <name> [<setting>...]
Fetch refs from a user's fork:
  git hub fetch [--ssh|--http|--git] <user> [<refspec>]
Fork a repo and clone it:
  git hub fork [--ssh|--http|--git] [--triangular [--upstream-branch=<branch>]] [<repo>]
List all forks of this repository:
  git hub forks [<repo>]
Create a new gist from files or stdin:
  git hub gist [--description=<description>] <file>...
Show all gists for a user:
  git hub gists [<user>]
Show hooks that have been enabled:
  git hub hooks
Show gitignore patterns for one or more languages:
  git hub ignore [<language>...]
Show the IP addresses for github.com services in CIDR format:
  git hub ip-addresses [--git] [--hooks] [--importer] [--pages]
Show issue details or report an issue:
  git hub issue [<repo>] [--parent] [<issue>...]
List issues in a repository:
  git hub issues [<repo>] [--parent] [<filter>...]
Display github log for yourself or other users. Or for an organisation or a repo:
  git hub log [--type=<type>] [--count=<count>] [--verbose] [<what>]
Display the contents of a directory on GitHub:
  git hub ls [<dir>...]
Mirror a repository, or all repositories for a user:
  git hub mirror [--ssh|--http|--git] [--goblet] [<repo>]
Create a graphviz graph of followers and forks:
  git hub network [<level>]
Protect a branch against deletions, force-pushes and failed status checks:
  git hub protect [--enforcement-level=<level>] [--contexts=<contexts>] <branch>
List active branch protections:
  git hub protected
Lists all keys for a user:
  git hub public-keys [<user>]
Opens a pull request to merge your branch to an upstream branch:
  git hub pull-request [--issue=<issue>] [--yes] [<yours:theirs>]
Get the README for a repository:
  git hub readme [<repo>]
Create a release:
  git hub release [--draft] [--prerelease] <tag> [<releasename>]
List all releases:
  git hub releases [<repo>]
Remove a user as collaborator:
  git hub remove-collaborator <user>...
Remove deploy key by id:
  git hub remove-deploy-key <key>...
Remove a hook:
  git hub remove-hook <name>
Render a markdown document:
  git hub render [--save=<outfile>] <file>
List all repos of a user, by default yours:
  git hub repos [--no-forks] [<user>]
Let the octocat speak to you:
  git hub say [<msg>]
Set the remote 'origin' to github.:
  git hub set-origin [--ssh|--http|--git] [--triangular [--upstream-branch=<branch>]]
Set up goblet config based on GitHub config:
  git hub setup-goblet
Display current and historical GitHub service status:
  git hub status
Remove branch protections from a branch:
  git hub unprotect <branch>
Display GitHub user info:
  git hub whoami
Display GitHub user info:
  git hub whois <user>...

Add an account to the configuration:
  git lab add-account [--host=<host>] <alias>
Add a project member:
  git lab add-member [--access-level=guest|reporter|developer|master|owner] <user>...
Adds keys to your public keys:
  git lab add-public-keys [<key>...]
Add user's fork as a named remote. The name defaults to the user's loginname:
  git lab add-remote [--ssh|--http] <user> [<name>]
Applies a merge request as a series of cherry-picks:
  git lab apply-merge <merge-request-number>
Open the GitLab page for a repository in a browser:
  git lab browse [--parent] [<repo>] [<section>]
Show a timeline of a user's activity:
  git lab calendar [<user>]
Display the contents of a file on GitLab:
  git lab cat <file>...
Clone a repository by name:
  git lab clone [--ssh|--http] [--triangular [--upstream-branch=<branch>]] [--parent] [git-clone-options] <repo> [<dir>]
Configure git-spindle, similar to git-config:
  git lab config [--unset] <key> [<value>]
Create a repository on gitlab to push to:
  git lab create [--private|--internal] [--group=<group>] [--description=<description>]
Fetch refs from a user's fork:
  git lab fetch [--ssh|--http] <user> [<refspec>]
Fork a repo and clone it:
  git lab fork [--ssh|--http] [--triangular [--upstream-branch=<branch>]] [<repo>]
Show issue details or report an issue:
  git lab issue [<repo>] [--parent] [<issue>...]
List issues in a repository:
  git lab issues [<repo>] [--parent] [<filter>...]
Display GitLab log for a repository:
  git lab log [<repo>]
Display the contents of a directory on GitLab:
  git lab ls [<dir>...]
List repo memberships:
  git lab members [<repo>]
Opens a merge request to merge your branch to an upstream branch:
  git lab merge-request [--yes] [<yours:theirs>]
Mirror a repository, or all your repositories:
  git lab mirror [--ssh|--http] [--goblet] [<repo>]
Protect a branch against force-pushes:
  git lab protect <branch>
List protected branches:
  git lab protected
Lists all keys for a user:
  git lab public-keys [<user>]
Remove a user's membership:
  git lab remove-member <user>...
List all your repos:
  git lab repos [--no-forks]
Set the remote 'origin' to gitlab.:
  git lab set-origin [--ssh|--http] [--triangular [--upstream-branch=<branch>]]
Remove force-push protection from a branch:
  git lab unprotect <branch>
Display GitLab user info:
  git lab whoami
Display GitLab user info:
  git lab whois <user>...

Add an account to the configuration:
  git bb add-account <alias>
Add a deploy key:
  git bb add-deploy-key <key>...
Add privileges for a user to this repo:
  git bb add-privilege [--admin|--read|--write] <user>...
Adds keys to your public keys:
  git bb add-public-keys [<key>...]
Add user's fork as a named remote. The name defaults to the user's loginname:
  git bb add-remote [--ssh|--http] <user> [<name>]
Applies a pull request as a series of cherry-picks:
  git bb apply-pr <pr-number>
Open the GitHub page for a repository in a browser:
  git bb browse [--parent] [<repo>] [<section>]
Display the contents of a file on BitBucket:
  git bb cat <file>...
Clone a repository by name:
  git bb clone [--ssh|--http] [--triangular [--upstream-branch=<branch>]] [--parent] [git-clone-options] <repo> [<dir>]
Configure git-spindle, similar to git-config:
  git bb config [--unset] <key> [<value>]
Create a repository on bitbucket to push to:
  git bb create [--private] [--team=<team>] [--description=<description>]
Lists all keys for a repo:
  git bb deploy-keys [<repo>]
Fetch refs from a user's fork:
  git bb fetch [--ssh|--http] <user> [<refspec>]
Fork a repo and clone it:
  git bb fork [--ssh|--http] [--triangular [--upstream-branch=<branch>]] [<repo>]
List all forks of this repository:
  git bb forks [<repo>]
Invite users to collaborate on this repository:
  git bb invite [--read|--write|--admin] <email>...
Show issue details or report an issue:
  git bb issue [<repo>] [--parent] [<issue>...]
List issues in a repository:
  git bb issues [<repo>] [--parent] [<filter>...]
Display the contents of a directory on BitBucket:
  git bb ls [<dir>...]
Mirror a repository, or all repositories for a user:
  git bb mirror [--ssh|--http] [--goblet] [<repo>]
List repo privileges:
  git bb privileges [<repo>]
Lists all keys for a user:
  git bb public-keys [<user>]
Opens a pull request to merge your branch to an upstream branch:
  git bb pull-request [--yes] [<yours:theirs>]
Remove deploy key by id:
  git bb remove-deploy-key <key>...
Remove a user's privileges:
  git bb remove-privilege <user>...
List all repos of a user, by default yours:
  git bb repos [--no-forks] [<user>]
Set the remote 'origin' to github.:
  git bb set-origin [--ssh|--http] [--triangular [--upstream-branch=<branch>]]
Create a new snippet from files or stdin:
  git bb snippet [--description=<description>] <file>...
Show all snippets for a user:
  git bb snippets [<user>]
Display BitBucket user info:
  git bb whoami
Display GitHub user info:
  git bb whois <user>...

Copyright (C) 2012-2018 Dennis Kaarsemaker <dennis@kaarsemaker.net>

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.
