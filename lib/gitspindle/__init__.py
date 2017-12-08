import gitspindle.monkey
import docopt
import os
import re
import shlex
import six
import sys
import tempfile
import time
import whelk
try:
    import importlib.util
except ImportError:
    # No plugins for you...
    importlib = None

__all__ = ['GitSpindle', 'Credential', 'command', 'wants_parent']
NO_VALUE_SENTINEL = 'NO_VALUE_SENTINEL'
PLUGIN_PATH = os.path.join(os.path.expanduser('~'), '.local', 'lib', 'git-spindle')

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

class DocoptExit(SystemExit):
    help = ''
    commands = {}
    def __init__(self, message='', command=None):
        if command and command in self.commands:
            SystemExit.__init__(self, self.commands[command])
        elif message:
            SystemExit.__init__(self, message)
        else:
            SystemExit.__init__(self, self.help)
docopt.DocoptExit = DocoptExit

def extras(help, version, options, doc):
    if not help or not any((o.name in ('-h', '--help')) and o.value for o in options):
        return
    for opt in options[1:]:
        if isinstance(opt, docopt.Argument):
            raise(DocoptExit(command=opt.value))
    raise DocoptExit()

docopt.extras = extras

GitSpindlePlugin = None
class GitSpindlePluginLoader(type):
    def __new__(cls, name, parents, attrs):
        if not importlib:
            return super(GitSpindlePluginLoader, cls).__new__(cls, name, parents, attrs)
        if GitSpindlePlugin in parents:
            for attr in attrs:
                if getattr(attrs[attr], 'is_command', False) :
                    if attr in GitSpindlePluginLoader.currently_loading:
                        print("%s is trying to override %s, ignoring" % (GitSpindlePluginLoader.current_plugin, attr))
                    else:
                        GitSpindlePluginLoader.currently_loading[attr] = attrs[attr]
        else:
            GitSpindlePluginLoader.currently_loading = attrs
            path = os.path.join(PLUGIN_PATH, name.lower())
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.endswith('.py'):
                        spec = importlib.util.spec_from_file_location('temp_module', os.path.join(path, file))
                        module = importlib.util.module_from_spec(spec)
                        GitSpindlePluginLoader.current_plugin = file
                        try:
                            spec.loader.exec_module(module)
                        except Exception as e:
                            print("Failed to load plugin %s: %s" % (file, str(e)))

            return super(GitSpindlePluginLoader, cls).__new__(cls, name, parents, attrs)

@six.add_metaclass(GitSpindlePluginLoader)
class GitSpindlePlugin(object):
     pass

@six.add_metaclass(GitSpindlePluginLoader)
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
        self.use_credential_helper = self.git('config', 'credential.helper').stdout.strip() not in ('', 'cache')

        self.usage = DocoptExit.help = """%s - %s integration for git
A full manual can be found on http://seveas.github.com/git-spindle/

Usage:\n""" % (self.prog, self.what)
        DocoptExit.help += "  %s [options] <command> [command-options]\n\nCommands:\n" % (self.prog)
        for name in sorted(dir(self)):
            fnc = getattr(self, name)
            if not getattr(fnc, 'is_command', False):
                continue
            if name.endswith('_'):
                name = name[:-1]
            name = name.replace('_', '-')
            self.commands[name] = fnc
            doc = [line.strip() for line in fnc.__doc__.splitlines()]
            if self.__class__.__name__ == 'BitBucket' and name == 'add-account':
                doc[0] = doc[0].replace('[--host=<host>] ', '')
            if doc[0]:
                doc[0] = ' ' + doc[0]
            help = '%s:\n  %s %s %s%s\n' % (doc[1], self.prog, '[options]', name, doc[0])
            self.usage += help
            DocoptExit.commands[name] = help
            DocoptExit.help += '  %-25s%s\n' % (name, doc[1])
        tail = """
Options:
  -h --help              Show this help message and exit
  --desc=<description>   Description for the new gist/repo
  --parent               Use the parent of a forked repo
  --yes                  Automatically answer yes to questions
  --issue=<issue>        Turn this issue into a pull request
  --http                 Use https:// urls for cloning 3rd party repos
  --ssh                  Use ssh:// urls for cloning 3rd party repos
  --git                  Use git:// urls for cloning 3rd party repos
  --goblet               When mirroring, set up goblet configuration
  --account=<account>    Use another account than the default\n"""
        self.usage += tail
        DocoptExit.help += tail

    def gitm(self, *args, **kwargs):
        """A git command that must be successful"""
        result = self.git(*args, **kwargs)
        if not result:
            if result.stderr:
                sys.stderr.write(result.stderr)
            sys.exit(result.returncode)
        return result

    def config(self, key, value=NO_VALUE_SENTINEL):
        if key in ('token', 'password') and self.use_credential_helper:
            return self.config_secret(key, value)
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

    def config_secret(self, key, value=NO_VALUE_SENTINEL):
        url = urlparse.urlparse(self.api_root())
        credential = Credential(protocol=url.scheme, host=url.hostname, path=url.path, username=self.my_login or self.config('user'), password=value)
        if value == NO_VALUE_SENTINEL:
            credential.password = ''
            credential.fill_noninteractive()
            return credential.password
        elif value is None:
            credential.reject()
        else:
            credential.approve()

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
        #   - Is it owned by the current account? Yes -> return it('s parent), No -> remember it
        # If we haven't found one owned by the current account:
        #   - Do we have one named origin? Yes -> return it('s parent)
        #   - Return the first remembered one('s parent)
        #  FIXME: errors should mention account if available
        remote = host = repo = None
        if opts['<repo>']:
            host, user, repo = self._parse_url(opts['<repo>'])
            if not repo:
                err("Repository %s could not be found" % opts['<repo>'])
        elif not self.in_repo:
            # Let git tell the user that we don't know what to do
            self.gitm('rev-parse')
        else:
            confremotes = self.git('config', '--get-regexp', 'remote\..*\.url').stdout.strip().splitlines()
            first = origin = None
            for remote in confremotes:
                remote, url = remote.split()
                remote = remote.split('.')[1]
                host, user, repo = self._parse_url(url)
                if repo and not first:
                    first = remote, host, user, repo
                if remote == 'origin':
                    origin = remote, host, user, repo
                if user == self.my_login:
                    break
            else:
                if origin:
                    remote, host, user, repo = origin
                elif first:
                    remote, host, user, repo = first

        if hostname_only:
            return host
        if not repo:
            remote, user, repo  = None, self.my_login, os.path.basename(self.repo_root())
        if repo and repo.endswith('.git'):
            repo = repo[:-4]

        repo_ = self.get_repo(remote, user, repo)

        if not repo_:
            err("Repository %s/%s could not be found on %s" % (user, repo, self.what))

        repo_.remote = remote
        if opts['--parent'] or opts['--maybe-parent']:
            parent = self.parent_repo(repo_)
            if parent:
                repo_ = parent
                repo_.remote = None
            elif opts['--parent']:
                err("No parent repo found for %s/%s" % (user, repo))

        return repo_

    def wait_for_repo(self, user, repo_, opts):
        warned = False
        tries = 120/5
        repo = None
        while tries and not repo:
            repo = self.get_repo('', user, repo_)
            if repo:
                res = self.git('ls-remote', self.clone_url(repo, opts))
                if res:
                    if warned:
                        print("")
                    return
                repo = None
            if not warned:
                sys.stdout.write("Waiting for repository creation...")
                warned = True
            else:
                sys.stdout.write('.')
            sys.stdout.flush()
            tries -= 1
            time.sleep(5)
        print("")
        err("%s failed to create the %s/%s repository" % (self.what, user, repo))

    def question(self, question, default=True):
        yn = ['y/N', 'Y/n'][default or self.assume_yes]
        if self.assume_yes:
            print("%s [%s] Y" % (question, yn))
            return True
        answer = raw_input("%s [%s] " % (question, yn))
        if not answer:
            return default
        return answer.lower() == 'y'

    def edit_msg(self, title, body, extra, filename, split_title=True):
        markdown = filename.endswith(('.md', '.MD'))
        comment = '[//]: #' if markdown else '#'
        if extra:
            extra = '\n\n' + comment + ' ' + extra.rstrip().replace('#', comment).replace('\n', '\n' + comment + ' ')
        else:
            extra = ''
        msg = body.rstrip() + extra
        if title:
            msg = title + '\n\n' + msg
        if self.git('rev-parse'):
            temp_file = os.path.join(self.gitm('rev-parse', '--git-dir').stdout.strip(), filename)
        else:
            fd, temp_file = tempfile.mkstemp(prefix=filename)
            os.close(fd)
        with open(temp_file, 'w') as fd:
            fd.write(msg)
        editor = shlex.split(self.gitm('var', 'GIT_EDITOR').stdout) + [temp_file]
        self.shell[editor[0]](*editor[1:], redirect=False)
        with open(temp_file) as fd:
            msg = try_decode(fd.read())
        os.unlink(temp_file)
        msg = re.compile('^' + re.escape(comment) + '.*(:?\n|$)', re.MULTILINE).sub('', msg).strip()
        if not split_title:
            return msg
        title, body = (msg + '\n').split('\n', 1)
        title = title.strip()
        body = body.strip()
        return title, body

    def backup_message(self, title, body, filename):
        msg = "%s\n\n%s" % (title, body)
        fd, temp_file = tempfile.mkstemp(prefix=filename)
        with os.fdopen(fd,'w') as fd:
            fd.write(msg)
        return temp_file

    def repo_root(self):
        root = self.shell.git('rev-parse', '--show-toplevel').stdout.strip()
        if not root:
            root = self.shell.git('rev-parse', '--git-dir').stdout.strip()
        root = os.path.abspath(root)
        return root

    def rel2root(self, path):
        if path.startswith('/'):
            return os.path.normpath(path)
        path = os.path.abspath(path)
        root = self.repo_root()
        if not path.startswith(root):
            raise ValueError("Path not inside the git repository")
        path = path.replace(root, '')
        return path

    def set_tracking_branches(self, remote, upstream=None, triangular=False, upstream_branch=None):
        if triangular and upstream:
            pushremote = remote
            pullremote = upstream
            self.gitm('config', 'remote.pushDefault', pushremote)
        else:
            pushremote = None
            pullremote = remote
            upstream_branch = None

        for branch in self.git('for-each-ref', 'refs/heads/**').stdout.strip().splitlines():
            branch = branch.split(None, 2)[-1][11:]

            if upstream_branch and self.git('for-each-ref', 'refs/remotes/%s/%s' % (pullremote, upstream_branch)).stdout.strip():
                tracking_remote = pullremote
                tracking_branch = upstream_branch
            elif self.git('for-each-ref', 'refs/remotes/%s/%s' % (pullremote, branch)).stdout.strip():
                tracking_remote = pullremote
                tracking_branch = branch
            elif pushremote and self.git('for-each-ref', 'refs/remotes/%s/%s' % (pushremote, branch)).stdout.strip():
                tracking_remote = pushremote
                tracking_branch = branch
            else:
                tracking_remote = None
                tracking_branch = None

            if tracking_remote and tracking_branch:
                current = self.git('config', 'branch.%s.remote' % branch).stdout.strip()
                if current in [remote, upstream, '']:
                    print("Configuring branch %s to track branch %s on remote %s" % (branch, tracking_branch, tracking_remote))
                    self.gitm('config', 'branch.%s.remote' % branch, tracking_remote)
                    self.gitm('config', 'branch.%s.merge' % branch, 'refs/heads/%s' % tracking_branch)

            if pushremote and self.git('for-each-ref', 'refs/remotes/%s/%s' % (pushremote, branch)).stdout.strip():
                current = self.git('config', 'branch.%s.pushremote' % branch).stdout.strip()
                if current in [remote, upstream, '']:
                    print("Configuring branch %s to push to remote %s" % (branch, pushremote))
                    self.gitm('config', 'branch.%s.pushremote' % branch, pushremote)

    def main(self):
        argv = self.prog.split()[1:] + sys.argv[1:]
        opts = docopt.docopt(self.usage, argv)
        self.assume_yes = opts['--yes']
        hosts = self.git('config', '--file', self.config_file, '--get-regexp', '%s\..*\.host' % self.spindle).stdout.strip()

        for (account, host) in [x.split() for x in hosts.splitlines()]:
            account = account.split('.')
            if host.startswith(('http://', 'https://')):
                host = urlparse.urlparse(host).hostname
            self.accounts[host] = account[1]
            self.hosts.append(host)

        # Which account do we use?
        # 1: Explicitly configured
        self.account = opts['--account'] or os.environ.get('GITSPINDLE_ACCOUNT', None)
        if self.account and not self.config('user') and not opts['config']:
            err("%s does not yet know about %s. Use %s add-account to configure it" % (self.prog, self.account, self.prog))

        # 2: Determine from the current repo
        if not self.account and (self.in_repo or opts['<repo>']):
            host = self.repository(opts, True)
            if host in self.accounts:
                self.account = self.accounts[host]
                self.hosts = [host]

        # 3: If we have no [gitXXX], but do have [gitXXX "url"], use it.
        if not self.account and not self.config('user'):
            accounts = self.git('config', '--file', self.config_file, '--get-regexp', '%s\..*\.user' % self.spindle).stdout.strip()
            if accounts:
                self.account = accounts.splitlines()[0].split('.')[1]

        os.environ['GITSPINDLE_ACCOUNT'] = self.account or self.spindle
        host = self.config('host')
        if host:
            if '://' not in host and ':' in host:
                # SSH host, transform to ssh:// syntax
                host = 'ssh://' + host.replace(':', '/')
            self.hosts = [urlparse.urlparse(host).hostname]

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
        if opts.get('--host', None):
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
        """[--keys] [--repos] [--gists] [--namespace=<namespace>]
        Delete all keys and repos of an account, used in tests"""
        if not self.my_login.startswith('git-spindle-test-'):
            raise RuntimeError("Can only clean up test accounts")

        namespace =  opts['--namespace'] or self.my_login

        if self.api.__name__ == 'github3':
            if opts['--keys']:
                for key in self.gh.iter_keys():
                    key.delete()
            if opts['--repos']:
                if namespace != self.my_login:
                    for repo in self.gh.organization(namespace).iter_repos():
                        print(repo)
                        if not repo.delete():
                            raise RuntimeError("Deleting repository failed")
                else:
                    for repo in self.gh.iter_repos():
                        if repo.owner.login == namespace:
                            print(repo)
                            if not repo.delete():
                                raise RuntimeError("Deleting repository failed")
                # it needs some time until the /user/repos endpoint recognized that the repos are deleted
                # this is a bug GitHub is working on to get a fix, maybe some caching issue on their side
                # so this code might be removed in the future
                # wait for the deletions to be recognized, or the test assertions might fail later on
                tries = 120/5
                clean = False
                while tries and not clean:
                    clean = namespace not in [x.owner.login for x in self.gh.iter_repos()]
                    if not clean:
                        tries -= 1
                        time.sleep(5)
                if not clean:
                    raise RuntimeError("Deleting repositories failed, try again in some minutes or increase the wait timeout in test_cleanup")
            if opts['--gists']:
                for gist in self.gh.iter_gists():
                    gist.delete()

        elif self.api.__name__ == 'gitspindle.bbapi':
            if opts['--keys']:
                for key in self.me.keys():
                    key.delete()
            if opts['--repos']:
                if namespace != self.my_login:
                    for repo in self.bb.team(namespace).repositories():
                        repo.delete()
                else:
                    for repo in self.me.repositories():
                        repo.delete()
            if opts['--gists']:
                for snippet in self.me.snippets():
                    snippet.delete()

        elif self.api.__name__ == 'gitspindle.glapi':
            if opts['--keys']:
                for key in self.me.Key():
                    key.delete()
            if opts['--repos']:
                for repo in self.gl.Project():
                    if repo.namespace.path == namespace:
                        repo.delete()

        else:
            raise UtterConfusion()

class Credential(object):
    shell = whelk.Shell(encoding='utf-8')
    params = ['protocol', 'host', 'path', 'username', 'password']

    def __init__(self, protocol, host, path='', username='', password=''):
        self.protocol = protocol
        self.host = host
        self.path = path
        self.username = username
        self.password = password

    def __str__(self):
        return '%s://%s:%s@%s/%s' % (self.protocol, self.username, self.password, self.host, self.path)

    def __repr__(self):
        return '<Credential %s>' % str(self)

    def fill(self):
        self.communicate('fill')

    def fill_noninteractive(self):
        env = os.environ.copy()
        env['GIT_TERMINAL_PROMPT'] = '0'
        env.pop('GIT_ASKPASS', None)
        env.pop('SSH_ASKPASS', None)
        self.communicate('fill', env=env)

    def approve(self):
        if not self.username or not self.password:
            raise ValueError("No username or password specified")
        self.communicate('approve')

    def reject(self):
        if not self.username:
            raise ValueError("No username specified")
        self.communicate('reject')
        self.password = ''

    def communicate(self, action, env=os.environ):
        data = self.format() + '\n\n'
        if env.get('GIT_TERMINAL_PROMPT', None) == '0':
            ret = self.shell.git('-c', 'core.askpass=', 'credential', action, env=env, input=data)
        else:
            ret = self.shell.git('credential', action, env=env, input=data)
        if not ret:
            if 'terminal prompts disabled' not in ret.stderr:
                raise RuntimeError("git credential %s failed: %s" % (action, ret.stderr))
        self.parse(ret.stdout)

    def format(self):
        return '\n'.join(['%s=%s' % (x, getattr(self, x)) for x in self.params if getattr(self, x)])

    def parse(self, text):
        for key, val in [line.split('=', 1) for line in text.splitlines() if line]:
            if key not in self.params:
                raise ValueError("Unexpected data: %s=%s" % (key, val))
            setattr(self, key, val)

# The main entrypoints
def hub():
    from gitspindle.github import GitHub
    GitHub().main()

def lab():
    from gitspindle.gitlab import GitLab
    GitLab().main()

def bucket():
    from gitspindle.bitbucket import BitBucket
    BitBucket().main()

def bb():
    from gitspindle.bitbucket import BitBucket
    BitBucket.prog = 'git bb'
    BitBucket().main()
