==========================
Github integration for git
==========================

With this git subcommand, you can perform various github actions, such as
creating or forking a repository from the command line.

Installation
============

To install the latest released version::

    pip install hub

To install the latest development version::

    pip install http://seveas.net/git-hub

Documentation
=============

http://pythonhosted.org/hub/

http://seveas.github.com/git-hub

Usage
=====

Add a service hook::

    $ git hub add-hook [name] [setting ...]

Adds the keys to your public keys (defaults to all keys it can find)::

    $ git hub add-public-keys [keys]

Add user's fork as a remote by that name::

    $ git hub add-remote [user]

Browse the repo (or its parent) on github::

    $ git hub browse [--parent]

Show a timeline of a user's activity::

    $ git hub calendar [user]

Display a file as present on github::

    $ git hub cat [file]

Clone one of your repositories by name::

    $ git hub clone [repo]

Create a repository on github to push to::

    $ git hub create

Edit a service hook::

    $ git hub edit-hook [name] [setting ...]

Fork a repo and clone it::

    $ git hub fork [url or user and repo]

List all forks of this repository::

    $ git hub forks

Create a new gist from files::

    $ git hub gist [files]

List a users gists::

    $ git hub gists [user]

List service hooks::

    $ git hub hooks

Issue details::

    $ git hub issue [issue number ...]

List issues::

    $ git hub issues [filters]

Display github action logs for users or repos::

    $ git hub log [what]

Mirror a repo or update it::

    $ git hub mirror [repo]

Create a graphviz graph of followers and forks::

    $ git hub network

Opens a pull request to merge your branch1 to upstream branch2
(defaults are current branch and master)::

    $ git hub pull-request [branch1:branch2]

Remove a service hook::

    $ git hub remove-hook [name]

Render a markdown page and show it in your browser::

    $ git hub render [file]

List all repos of a user, by default yours::

    $ git hub repos [user]

Set the remote 'origin' to github. If this is a fork,
set the remote 'upstream' to the parent::

    $ git hub set-origin

Show the last few GitHub status messages::

    $ git hub status

Display github user info::

    $ git hub whoami

Display github user info::

    $ git hub whois [user ...]

Copyright & License
=====================

Copyright (C) 2012-2014 Dennis Kaarsemaker <dennis@kaarsemaker.net>

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.
