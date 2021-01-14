Plugins for spindles
====================

.. note::
   Plugins only work when using python 3. Python 2's importlib does not
   contain the necessary functionality.

As of version 3.4, git-spindle has a plugin system with which you can add
subcommands that are not suitable for sending upstream. For example, I use it
for enumerating the status of my work PR's that assumes access to work internal
systems.

Plugins live in `~/.local/lib/git-spindle/$spindle/$plugin.py`. They are
structured like the actual spindles themselves, except that your methods must
be fully self-contained as they will be transplanted into the main spindle
classes. Methods must comply with the following:

* They must be decorated with `@command`, else they will be ignored They must
* have documentation as a 2-line strinf. The first line must be a docpt-format
* list of accepted options. The second line contains a short usage
  string. If the method takes no options, the docstring must start with a
  newline.
* Since the method is transplanted into the actual spindle, the method must be
  completely self-contained. The 'self' argument will also be an instance of
  the spindle, not the plugin
* The self argument may rely on certain GitSpindle internals, for which you're
  going to have to read the code:

  - `self.api` will refer to the api module
  - `self.spindle` is the name of the spindle
  - `self.gh/self.bb/self.gl` refer to the authenticated api instance
  - `self.shell` is a `whelk.Shell` instance with utf-8 encoding
  - the `self.git` function to execute git commands
  - the `self.gitm` function that does the same, but exits if the command fails
  - the `self.config` function to read/write git-spindle configuration
  - the `self.repository` function, that finds the correct repository on
    GitHub/GitLab/Bitbucket
* Use of other internals is discouraged. If there is another internal function
  you would like to use (or add), please file a pull request.

Here is a minimal example that prints a summary of all pull requests you've
filed in an organization's repositories::

   from gitspindle import GitSpindlePlugin, command
   
   class GitHub(GitSpindlePlugin):
       @command
       def my_org_prs(self, opts):
           """<org>
              List the PR's you filed in an organization's repos"""
           for issue in self.gh.iter_org_issues(opts['<org>'], filter='created'):
               if issue.pull_request:
                   rl = '[%s/%s]' % issue.repository
                   print('%-25s %s %s' % (rl, issue.title, issue.html_url))

Placing this in `~/.local/lib/git-spindle/github/org-prs.py` will cause `git hub
my-org-prs someorgname` to work, including adding the usage string to the main
program's help functions.
