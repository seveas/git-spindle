import gitspindle.monkey
import docopt
import os
import re
import shlex
import sys
import tempfile
import whelk

__all__ = ['GitSpindle', 'command', 'wants_parent']
NO_VALUE_SENTINEL = 'NO_VALUE_SENTINEL'

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

def command(fnc):
    fnc.is_command = True
    if not hasattr(fnc, 'no_login'):
        fnc.no_login = False
    if not hasattr(fnc, 'wants_parent'):
        fnc.wants_parent = False
    return fnc
hidden_command = lambda fnc: os.getenv('DEBUG') and command(fnc)

def wants_parent(fnc):
    fnc.wants_parent = True
    return fnc

def no_login(fnc):
    fnc.no_login = True
    return fnc

class GitSpindle(object):

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
        self.accounts = {}
        self.my_login = {}
        self.usage = """%s - %s integration for git
A full manual can be found on http://seveas.github.com/git-spindle/

Usage:\n""" % (self.prog, self.what)
        for name in sorted(dir(self)):
            fnc = getattr(self, name)
            if not getattr(fnc, 'is_command', False):
                continue
            if name.endswith('_'):
                name = name[:-1]
            name = name.replace('_', '-')
            self.commands[name] = fnc
            self.usage += ('  %s %s %s %s\n' % (self.prog, '[options]', name, fnc.__doc__.split('\n', 1)[0].strip()))
        self.usage += """
Options:
  -h --help              Show this help message and exit
  --desc=<description>   Description for the new gist/repo
  --parent               Use the parent of a forked repo
  --issue=<issue>        Turn this issue into a pull request
  --http                 Use https:// urls for cloning 3rd party repos
  --ssh                  Use ssh:// urls for cloning 3rd party repos
  --git                  Use git:// urls for cloning 3rd party repos
  --goblet               When mirroring, set up goblet configuration
  --account=<account>    Use another account than the default\n"""

    def gitm(self, *args, **kwargs):
        """A git command thas must be succesfull"""
        result = self.git(*args, **kwargs)
        if not result:
            if result.stderr:
                sys.stderr.write(result.stderr)
            sys.exit(result.returncode)
        return result

    def config(self, key, value=NO_VALUE_SENTINEL):
        section = self.spindle
        if self.account:
            section = '%s.%s' % (self.spindle, self.account)
        key = '%s.%s' % (section, key)
        if value is NO_VALUE_SENTINEL:
            result = self.git('config', '--file', self.config_file, key)
            if result.returncode not in (0, 1): # 128 is returned for parse errors
                print(result.stderr.rstrip())
                sys.exit(result.returncode)
            return result.stdout.strip()
        elif value is None:
            self.gitm('config', '--file', self.config_file, '--unset', key)
        else:
            try:
                umask = os.umask(63) # 0x077
                return self.gitm('config', '--file', self.config_file, key, value)
            finally:
                os.umask(umask)

    def _parse_url(self, url):
        if '://' not in url and ':' in url:
            # SSH url, transform to ssh:// syntax
            url = 'ssh://' + url.replace(':', '/')
        url = urlparse.urlparse(url)
        if url.hostname and url.hostname not in self.hosts:
            return [None, None, None]
        return [url.hostname] + self.parse_url(url)

    def remotes(self):
        confremotes = self.git('config', '--get-regexp', 'remote\..*\.url').stdout.strip().splitlines()
        ret = {}
        for remote in confremotes:
            remote, url = remote.split()
            remote = remote.split('.')[1]
            ret[remote] = url
        return ret

    def repository(self, opts, hostname_only=False):
        # How do we select a repo?
        # - Did we request one with --repo?
        # - Else we look at remotes
        #   - Do we recognize the host? No -> discard
        #   - Do we have an account? Is it on there? No -> discard
        #   - Is it mine? Yes -> return it('s parent), No -> remember it
        #   - Return the first rememered one(s parent)
        #  FIXME: errors should mention account if available
        remote = host = None
        if opts['<repo>']:
            host, user, repo = self._parse_url(opts['<repo>'])
            if not repo:
                err("Repository %s could not be found" % opts['<repo>'])
        elif not self.in_repo:
            # Let git tell the user that we don't know what to do
            self.gitm('rev-parse')
        else:
            confremotes = self.git('config', '--get-regexp', 'remote\..*\.url').stdout.strip().splitlines()
            first = None
            for remote in confremotes:
                remote, url = remote.split()
                remote = remote.split('.')[1]
                host, user, repo = self._parse_url(url)
                if repo and not first:
                    first = host, user, repo
                if user == self.my_login:
                    break
            else:
                if first:
                    host, user, repo = first

        if hostname_only:
            return host
        if repo and repo.endswith('.git'):
            repo = repo[:-4]
        if not repo:
            remote, user, repo  = None, self.my_login, os.path.basename(os.getcwd())
        repo_ = self.get_repo(remote, user, repo)

        if not repo_:
            err("Repository %s/%s could not be found on %s" % (user, repo, self.what))

        if opts['--parent'] or opts['--maybe-parent']:
            parent = self.parent_repo(repo_)
            if parent:
                repo_ = parent
            elif opts['--parent']:
                err("No parent repo found for %s/%s" % (user, repo))

        return repo_

    def edit_msg(self, msg, filename):
        if self.git('rev-parse'):
            temp_file = os.path.join(self.gitm('rev-parse', '--git-dir').stdout.strip(), filename)
        else:
            fd, temp_file = tempfile.mkstemp(prefix=filename)
            os.close(fd)
        with open(temp_file, 'w') as fd:
            fd.write(msg.encode('utf-8'))
        editor = shlex.split(self.gitm('var', 'GIT_EDITOR').stdout) + [temp_file]
        self.shell[editor[0]](*editor[1:], redirect=False)
        with open(temp_file) as fd:
            title, body = (try_decode(fd.read()) +'\n').split('\n', 1)
        os.unlink(temp_file)
        title = title.strip()
        body = body.strip()
        body = re.sub('^#.*', '', body, flags=re.MULTILINE).strip()
        return title, body

    def main(self):
        argv = self.prog.split()[1:] + sys.argv[1:]
        opts = docopt.docopt(self.usage, argv)
        self.account = opts['--account'] or os.environ.get('GITSPINDLE_ACCOUNT', None)
        if self.account and not self.config('user'):
            err("%s does not yet know about %s. Use %s add-account to configure it" % (self.prog, self.account, self.prog))
        hosts = self.git('config', '--file', self.config_file, '--get-regexp', '%s.*host' % self.spindle).stdout.strip()

        for (account, host) in [x.split() for x in hosts.splitlines()]:
            account = account.split('.')
            if host.startswith(('http://', 'https://')):
                host = urlparse.urlparse(host).hostname
            if len(account) == 2: # User has set a host for the default account
                self.hosts = [host]
            if self.account == account[1]:
                self.hosts = [host]
                break
            self.accounts[host] = account[1]
            self.hosts.append(host)

        if not self.account and (self.in_repo or opts['<repo>']):
            host = self.repository(opts, True)
            if host in self.accounts:
                self.account = self.accounts[host]
                self.hosts = [host]

        os.environ['GITSPINDLE_ACCOUNT'] = self.account or self.spindle

        for command, func in self.commands.items():
            if opts[command]:
                if not func.no_login:
                    self.login()
                opts['command'] = command
                if isinstance(opts[command], list):
                    opts['extra-opts'] = opts[command]
                    opts[command] = True
                else:
                    opts['extra-opts'] = []
                opts['--maybe-parent'] = func.wants_parent
                try:
                    func(opts)
                except KeyboardInterrupt:
                    sys.exit(1)
                break

    @command
    @no_login
    def add_account(self, opts):
        """[--host=<host>] <alias>
           Add an account to the configuration"""
        self.account = opts['<alias>']
        if opts['--host']:
            self.config('host', opts['--host'])
        self.login()

    @command
    @no_login
    def config_(self, opts):
        """[--unset] <key> [<value>]
           Configure git-spindle, similar to git-config"""
        key = opts['<key>'][0]
        value = opts['<value>']
        if '.' in key:
            err("Keys should be single-level only, the section is always the current account")
        if opts['--unset']:
            self.config(key, None)
        elif value is not None:
            self.config(key, value)
        else:
            print(self.config(key))

    # And debugging
    @hidden_command
    def run_shell(self, opts):
        """[-c <command>]
           Debug method to run a shell"""
        import code
        import readline
        import rlcompleter
        repo = None
        if self.in_repo or opts['<repo>']:
            repo = self.repository(opts)

        data = {
            'self':    self,
            'opts':    opts,
            'repo':    repo,
        }
        readline.set_completer(rlcompleter.Completer(data).complete)
        readline.parse_and_bind("tab: complete")
        shl = code.InteractiveConsole(data)
        if opts['<command>']:
            shl.runsource(opts['<command>'])
            sys.exit(0)
        else:
            shl.interact()
        sys.exit(1)

    @hidden_command
    def test_cleanup(self, opts):
        """\nDelete all keys and repos of an account, used in tests"""
        if 'test' not in self.my_login:
            raise RuntimeError("Can only clean up test accounts")

        if self.api.__name__ == 'github3':
            for key in self.gh.iter_keys():
                key.delete()
            for repo in self.gh.iter_repos():
                if repo.owner.login == self.my_login:
                    if not repo.delete():
                        raise RuntimeError("Deleting repository failed")

        elif self.api.__name__ == 'gitspindle.bbapi':
            for key in self.me.keys():
                key.delete()
            for repo in self.me.repositories():
                repo.delete()

        elif self.api.__name__ == 'gitspindle.glapi':
            for key in self.me.Key():
                key.delete()
            for repo in self.gl.Project():
                repo.delete()

        else:
            raise UtterConfusion()
