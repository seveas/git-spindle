import gitspindle.monkey
from gitspindle.singleton import Singleton
import docopt
import os
import re
import shlex
import sys
import whelk

__all__ = ['GitSpindle', 'command', 'needs_repo', 'needs_worktree']

__builtins__['PY3'] = sys.version_info[0] > 2
if PY3:
    import urllib.parse as urlparse
    # On python 3, shell decodes into utf-8 as above
    __builtins__['try_decode'] = lambda x: x
    # On python 3, raw_input has become input
    __builtins__['raw_input'] = input
else:
    import urlparse
    # Try decoding as utf-8 only
    __builtins__['try_decode'] = lambda x: x.decode('utf-8')

def err(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(1)
__builtins__['err'] = err

import pprint
__builtins__['pprint'] = pprint.pprint
del pprint

class Repository(object):
    spindle = 'gitspindle'
    owner = None
    def __init__(self, url):
        self.url = url

class GitSpindle(Singleton):
    spindle = 'gitspindle'
    prog = 'git spindle'
    what = ''

    def __init__(self):
        self.shell = whelk.Shell(encoding='utf-8')
        self.git = self.shell.git
        self.git_dir = self.git('rev-parse', '--git-dir')
        if self.git_dir.returncode == 0:
            self.git_dir = os.path.abspath(self.git_dir.stdout.strip())
        else:
            self.git_dir = None
        self.in_repo = bool(self.git_dir)
        self.config_file = os.path.join(os.path.expanduser('~'), '.gitspindle')
        xdg_dir = os.environ.get('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config'))
        xdg_file = os.path.join(xdg_dir, 'git', 'spindle')
        if os.path.exists(xdg_file):
            self.config_file = xdg_file
        self.commands = {}
        self.usage = """%s - %s integration for git
A full manual can be found on http://seveas.github.com/git-spindle/

Usage:\n""" % (self.prog, self.what)
        for name in sorted(dir(self)):
            fnc = getattr(self, name)
            if not getattr(fnc, 'is_command', False):
                continue
            name = name.replace('_', '-')
            self.commands[name] = fnc
            self.usage += ('  %s %s %s\n' % (self.prog, name, fnc.__doc__.split('\n', 1)[0].strip()))
        self.usage += """
Options:
  -h --help              Show this help message and exit
  --desc=<description>   Description for the new gist/repo
  --parent               Use the parent of a forked repo
  --issue=<issue>        Turn this issue into a pull request
  --ssh                  Use SSH for cloning 3rd party repos
  --http                 Use https for cloning 3rd party repos
  --goblet               When mirroring, set up goblet configuration\n"""

    def gitm(self, *args, **kwargs):
        """A git command thas must be succesfull"""
        result = self.git(*args, **kwargs)
        if not result:
            if result.stderr:
                print(result.stderr.rstrip())
            sys.exit(result.returncode)
        return result

    def config(self, key, value=None):
        if value is not None:
            try:
                umask = os.umask(63) # 0x077
                return self.git('config', '--file', self.config_file, key, value)
            finally:
                os.umask(umask)
        return self.git('config', '--file', self.config_file, key).stdout.strip()

    def backend_for_remote(self, remote, url):
        backend = self.git('config', 'remote.%s.spindle' % remote).stdout.strip()
        if not backend:
            if os.path.exists(url):
                return GitSpindle()
            if '://' not in url and ':' in url:
                # SSH url, transform to ssh:// syntax
                url = 'ssh://' + url.replace(':', '/')
            url = urlparse.urlparse(url)
            host = url.netloc
            if '@' in host:
                host = host[host.find('@') +1:]
            if host in ('gist.github.com', 'github.com', 'www.github.com'):
                backend = 'github'
            elif host in ('gitlab.com', 'www.gitlab.com'):
                backend = 'gitlab'
            elif host in ('bitbucket.org', 'www.bitbucket.org'):
                backend = 'bitbucket'
            elif host:
                backend = self.config('spindle.%s' % host)
        if backend == 'github':
            from gitspindle.github import GitHub
            return GitHub()
        elif backend == 'gitlab':
            from gitspindle.gitlab import GitLab
            return GitLab()
        elif backend == 'bitbucket':
            from gitspindle.bitbucket import BitBucket
            return BitBucket()
        else:
            return GitSpindle()

    def parse_repo(self, remote, url):
        return Repository(url)

    def get_remotes(self, opts):
        """Return all remotes as their respective objects in a dict {name:
           repo}"""
        remotes = {'.dwim': None, '.mine': None}
        first = None
        if opts['<repo>']:
            remotes['.dwim'] = remotes['opts'] = self.parse_repo(None, opts['<repo>'])

        if self.in_repo:
            confremotes = self.git('config', '--get-regexp', 'remote\..*\.url').stdout.strip().splitlines()
            for remote in confremotes:
                remote, url = remote.split()
                remote = remote.split('.')[1]
                repo = self.backend_for_remote(remote, url).parse_repo(remote, url)
                if not repo:
                    print("Repository %s no longer exists" % url)
                    continue
                repo.remote = remote
                if not first and (repo.spindle == self.spindle):
                    first = repo
                remotes[remote] = repo
                try:
                    if repo.owner == self.me and repo.spindle == self.spindle:
                        remotes['.mine'] = repo
                except AttributeError:
                    # github3.py throws this when comparing github3.py objects
                    # against regular ones
                    pass

        if not remotes['.dwim']:
            if remotes['.mine']:
                remotes['.dwim'] = remotes['.mine']
            elif 'origin' in remotes and remotes['origin'].spindle == self.spindle:
                remotes['.dwim'] = remotes['origin']
            elif 'upstream' in remotes and remotes['origin'].spindle == self.spindle:
                remotes['.dwim'] = remotes['upstream']
            elif first:
                remotes['.dwim'] = first
            elif self.in_repo:
                path = os.path.basename(self.shell.git('rev-parse', '--show-toplevel').stdout.strip())
                remotes['.dwim'] = self.parse_repo(None, path)

        if opts['--parent'] and remotes['.dwim']:
            parent = self.parent_repo(remotes['.dwim'])
            if parent:
                remotes['.dwim'] = parent

        return remotes

    def parent_repo(self, repo):
        return None

    def edit_msg(self, msg, filename):
        temp_file = os.path.join(self.gitm('rev-parse', '--git-dir').stdout.strip(), filename)
        with open(temp_file, 'w') as fd:
            fd.write(msg.encode('utf-8'))
        editor = shlex.split(self.gitm('var', 'GIT_EDITOR').stdout) + [temp_file]
        self.shell[editor[0]](*editor[1:], redirect=False)
        with open(temp_file) as fd:
            title, body = (try_decode(fd.read()) +'\n').split('\n', 1)
        title = title.strip()
        body = body.strip()
        body = re.sub('^#.*', '', body, flags=re.MULTILINE).strip()
        return title, body

    def main(self):
        argv = self.prog.split()[1:] + sys.argv[1:]
        opts = docopt.docopt(self.usage, argv)
        for command, func in self.commands.items():
            if opts[command]:
                opts['command'] = command
                if isinstance(opts[command], list):
                    opts['extra-opts'] = opts[command]
                    opts[command] = True
                else:
                    opts['extra-opts'] = []
                opts.update(func.opts)
                if func.needs_repo:
                    opts['remotes'] = self.get_remotes(opts)
                if func.needs_worktree and not self.in_repo:
                    err('%s only works from within a work tree' % command)
                try:
                    func(opts)
                except KeyboardInterrupt:
                    sys.exit(1)
                break

def command(fnc=None, **kwargs):
    if not fnc:
        return lambda func: command(func, **kwargs)
    fnc.opts = kwargs
    fnc.is_command = True
    if not hasattr(fnc, 'needs_repo'):
        fnc.needs_repo = '<repo>' in fnc.__doc__
    if not hasattr(fnc, 'needs_worktree'):
        fnc.needs_worktree = False
    return fnc

def needs_repo(fnc):
    fnc.needs_repo = True
    return fnc

def needs_worktree(fnc):
    fnc.needs_worktree = True
    return fnc
