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
To install the latest released version on Ubuntu::

    sudo add-apt-repository ppa:dennis/devtools
    sudo apt-get install git-spindle

To install the latest released version on Windows:

* Install git from http://git-for-windows.github.io/
* Install python 3.5 or newer from https://www.python.org/downloads/
* Run the following 2 commands in a command prompt::

    py -mensurepip
    py -mpip install git-spindle

To install the latest released version on other systems, assuming python and
pip are installed::

    pip install git-spindle

Contents
========

.. toctree::
   :maxdepth: 1

   github
   gitlab
   bitbucket
   plugins
