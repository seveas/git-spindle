Git subcommands for interacting with central services
=====================================================

Many central git hosting services, such as GitHub and GitLab, provide an API to
perform actions such as creating repositories and filing pull requests.
git-spindle is a collection of git subcommands to make using these services
easier.

For example, to fork and clone a repository on GitHub, one can now simply use::

    git hub clone seveas/whelk

Install info
------------
To install the latest released version::

    pip install git-spindle

If you use windows, you'll want to install git and pip via msys2. Download
`msys2 <http://msys2.github.io/>`_ and use pacman to install pip and git::

    pacman -Syu
    pacman -S git
    pacman -S mingw-w64-i686-python2-pip

Contents
========

.. toctree::
   :maxdepth: 1

   github
