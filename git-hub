#!/usr/bin/env python
#
# Github integration for git.
# Usage: See README
#
# Copyright (C) 2012-2013 Dennis Kaarsemaker <dennis@kaarsemaker.net>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

import getpass
import github3
import glob
import docopt
import os
import re
import socket
import sys
import webbrowser
from whelk import Shell
shell = Shell(encoding='utf-8')
if sys.version_info[0] > 2:
    # On python 3, shell decodes into utf-8 as above
    try_decode = lambda x: x
else:
    # Try decoding as utf-8 only
    try_decode = lambda x: x.decode('utf-8')

## ANSI color library from github.com/seveas/hacks
class Attr(object):
    def __init__(self, **attr):
        self.attr = attr
        self.rev_attr = dict([(v,k) for k,v in attr.items()])
        for k, v in attr.items():
            setattr(self, k, v)

    def name(self, val):
        return self.rev_attr[val]

fgcolor = Attr(black=30, red=31, green=32, yellow=33, blue=34, magenta=35, cyan=36, white=37, none=None)
bgcolor = Attr(black=40, red=41, green=42, yellow=43, blue=44, magenta=45, cyan=46, white=47, none=None)
attr    = Attr(normal=0, bright=1, faint=2, underline=4, negative=7, conceal=8, crossed=9, none=None)

esc = '\033'
mode = lambda *args: "%s[%sm" % (esc, ';'.join([str(x) for x in args if x is not None]))
reset = mode(attr.normal)
wrap = lambda text, *args: "%s%s%s" % (mode(*args), text, reset)

erase_line = esc + '[K'
erase_display = esc + '[2J'
save_cursor = esc + '[s'
restore_cursor = esc + '[u'
## End ansi color library

def main():
    usage = """github integration for git
A full manual can be found on http://seveas.github.com/git-hub

Usage:
  git-hub add-hook <name> [<setting>...]
  git-hub add-public-keys [<key>...]
  git-hub add-remote [--ssh|--http] <user>
  git-hub browse
  git-hub clone [--ssh|--http] <repo>
  git-hub create [-d <description>]
  git-hub edit-hook <name> [<setting>...]
  git-hub fork [--ssh|--http] <repo>
  git-hub forks
  git-hub gist [--desc <description>] <file>...
  git-hub gists [<user>]
  git-hub hooks
  git-hub ignore [<language>...]
  git-hub issue [--parent] <issue>...
  git-hub issues [--parent] [<filter>...]
  git-hub mirror [<repo>]
  git-hub network [<level>]
  git-hub public-keys <user>
  git-hub pull-request [--issue=<issue>] [<branch1:branch2>]
  git-hub remove-hook <name>
  git-hub repos [<user>]
  git-hub set-origin
  git-hub whoami
  git-hub whois <user>...

Options:
  -h --help              Show this help message and exit
  --desc=<description>   Description for the new gist/repo
  --parent               Show issues for the parent repo
  --issue=<issue>        Turn this issue into a pull request
  --ssh                  Use SSH for cloning 3rd party repos
  --http                 Use https for cloning 3rd party repos
"""

    opts = docopt.docopt(usage)
    for command in commands:
        if opts[command]:
            try:
                commands[command](opts)
            except KeyboardInterrupt:
                sys.exit(1)
            break

def err(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(1)

def check(result):
    if result.returncode != 0:
        print(result.stderr.rstrip())
        sys.exit(result.returncode)
    return result

commands = {}
def command(fnc):
    commands[fnc.__name__.replace('_','-')] = fnc
    return fnc

def github():
    config_file = os.path.join(os.path.expanduser('~'), '.githubconfig')
    old_umask = os.umask(63) # 0o077

    user = shell.git('config', '--file', config_file, 'github.user').stdout.strip()
    if not user:
        user = raw_input("Github user: ").strip()
        shell.git('config', '--file', config_file, 'github.user', user)

    token = shell.git('config', '--file', config_file, 'github.token').stdout.strip()
    if not token:
        password = getpass.getpass("GitHub password: ")
        auth = github3.authorize(user, password, ['user', 'repo', 'gist'],
                "Github Git integration on %s" % socket.gethostname(), "http://seveas.github.com/git-hub")
        token = auth.token
        shell.git('config', '--file', config_file, 'github.token', token)
        shell.git('config', '--file', config_file, 'github.auth_id', str(auth.id))

    if not user or not token:
        err("No user or token specified")
    gh = github3.login(username=user, token=token)
    try:
        gh.user()
    except github3.GitHubError:
        # Token obsolete
        shell.git('config', '--file', config_file, '--unset', 'github.token')
        gh = github()
    os.umask(old_umask)
    return gh

def get_repo():
    gh = github()
    root = check(shell.git('rev-parse', '--show-toplevel')).stdout.strip()
    name = os.path.basename(root)
    return gh.repository(gh.user().login, name)

@command
def create(opts):
    """Create a repository on github to push to"""
    root = check(shell.git('rev-parse', '--show-toplevel')).stdout.strip()
    name = os.path.basename(root)
    gh = github()
    if name in [x.name for x in gh.iter_repos()]:
        err("Repository already exists")
    gh.create_repo(name=name, description=opts['<description>'] or "")
    set_origin(opts)

@command
def set_origin(opts):
    """Set the remote 'origin' to github.\n  If this is a fork, set the remote 'upstream' to the parent"""
    repo = get_repo()
    shell.git('config', 'remote.origin.url', repo.ssh_url)
    shell.git('config', 'remote.origin.fetch', '+refs/heads/*:refs/remotes/origin/*')

    if repo.fork:
        parent = repo.parent
        shell.git('config', 'remote.upstream.url', parent.git_url)
        shell.git('config', 'remote.upstream.fetch', '+refs/heads/*:refs/remotes/upstream/*')

@command
def repos(opts):
    """[user] List all repos of a user, by default yours"""
    gh = github()
    user = (opts['<user>'] or [gh.user().login])[0]
    repos = list(gh.iter_repos(user))
    maxlen = max([len(x.name) for x in repos])
    fmt = "%%-%ds %%s" % maxlen
    for repo in repos:
        print(wrap(fmt % (repo.name, repo.description), attr.faint if repo.fork else attr.normal))

@command
def clone(opts):
    """Clone a repositories by name"""
    gh = github()
    if '/' in opts['<repo>']:
        user, repo = opts['<repo>'].rsplit('/',2)[-2:]
    else:
        user, repo = gh.user().login, opts['<repo>']
    if repo.endswith('.git'):
        repo = repo[:-4]

    repo = gh.repository(user, repo)
    url = repo.ssh_url
    if gh.user().login != user:
        url = repo.git_url
        if opts['--ssh']:
            url = repo.ssh_url
        elif opts['--http']:
            url = repo.clone_url

    rc = shell.git('clone', url, redirect=False).returncode
    if rc:
        sys.exit(rc)
    if repo.fork:
        os.chdir(repo.name)
        set_origin(opts)
        shell.git('fetch', 'upstream', redirect=False)

@command
def mirror(opts):
    gh = github()
    if not opts['<repo>']:
        # Update the current, mirrored repo
        repo = get_repo()
        if shell.git('config', 'core.bare').stdout != 'true' or \
           shell.git('config', 'remote.origin.mirror').stdout != 'true':
               err("This is not a mirrored repository")
        rc = shell.git('fetch', '-q', 'origin', redirect=False).returncode
        if rc:
            sys.exit(rc)
        shell.git('remote', 'prune', 'origin', redirect=False).returncode
        if rc:
            sys.exit(rc)
        with open('description', 'w') as fd:
            fd.write(repo.description)
        return

    if '/' in opts['<repo>']:
        user, repo = opts['<repo>'].rsplit('/',2)[-2:]
    else:
        user, repo = gh.user().login, opts['<repo>']
    if repo.endswith('.git'):
        repo = repo[:-4]

    repo = gh.repository(user, repo)
    url = repo.git_url
    if opts['--ssh']:
        url = repo.ssh_url
    elif opts['--http']:
        url = repo.clone_url

    rc = shell.git('clone', '--mirror', url, redirect=False).returncode
    if rc:
        sys.exit(rc)
    with open(os.path.join(repo.name + '.git', 'description'), 'w') as fd:
        fd.write(repo.description)

@command
def fork(opts):
    gh = github()
    """Fork a repo and clone it"""
    if '/' not in opts['<repo>']:
        err("Usage: git hub fork url\n       git hub fork user/repo")
    user, repo = opts['<repo>'].rsplit('/',2)[-2:]
    if repo.endswith('.git'):
        repo = repo[:-4]

    if repo in [x.name for x in gh.iter_repos()]:
        err("Repository already exists")
    repo = gh.repository(user, repo)
    my_clone = repo.create_fork()
    opts['<repo>'] = my_clone.name
    clone(opts)

@command
def forks(opts):
    """List all forks of this repository"""
    repo = get_repo()
    if repo.fork:
        repo = repo.parent
    print("[%s] %s" % (wrap(repo.owner.login, attr.bright), repo.html_url))
    for fork in repo.iter_forks():
        print("[%s] %s" % (fork.owner.login, fork.html_url))

@command
def issues(opts):
    """List issues"""
    repo = get_repo()
    if repo.fork and opts['--parent']:
        repo = repo.parent
    filters = dict([x.split('=', 1) for x in opts['<filter>']])
    for issue in repo.iter_issues(**filters):
        url = issue.pull_request and issue.pull_request['html_url'] or issue.html_url
        print("[%d] %s %s" % (issue.number, issue.title, url))

@command
def issue(opts):
    """Issue details"""
    repo = get_repo()
    if repo.fork and opts['--parent']:
        repo = repo.parent
    for issue in opts['<issue>']:
        issue = repo.issue(issue)
        print(wrap(issue.title, attr.bright, attr.underline))
        print(issue.body)
        print(issue.pull_request and issue.pull_request['html_url'] or issue.html_url)

@command
def add_remote(opts):
    """Add user's fork as a remote by that name"""
    repo = get_repo()
    if repo.fork:
        repo = repo.parent
    forks = repo.iter_forks()
    for fork in forks:
        if fork.owner.login in opts['<user>']:
            url = fork.git_url
            if opts['--ssh']:
                url = fork.ssh_url
            elif opts['--http']:
                url = fork.clone_url
            check(shell.git('remote', 'add', fork.owner.login, url))
            check(shell.git('fetch', fork.owner.login, stdout=False, stderr=False))

@command
def whois(opts):
    """Display github user info"""
    gh = github()
    for user in opts['<user>']:
        user = gh.user(user)
        print(wrap(user.name or user.login, attr.bright, attr.underline))
        print('Profile   %s' % user.html_url)
        if user.email:
            print('Email     %s' % user.email)
        if user.blog:
            print('Blog      %s' % user.blog)
        if user.location:
            print('Location  %s' % user.location)
        if user.company:
            print('Company   %s' % user.company)
        print('Repos     %d public, %d private' % (user.public_repos, user.total_private_repos))
        print('Gists     %d public, %d private' % (user.public_gists, user.total_private_gists))
        if user.login == gh.user().login:
            keys = gh.iter_keys()
        else:
            keys = user.iter_keys()
        for pkey in keys:
            algo, key = pkey.key.split()
            algo = algo[4:].upper()
            if pkey.title:
                print("%s key%s...%s (%s)" % (algo, ' ' * (6 - len(algo)), key[-10:], pkey.title))
            else:
                print("%s key%s...%s" % (algo, ' ' * (6 - len(algo)), key[-10:]))

@command
def whoami(opts):
    """Display github user info"""
    gh = github()
    opts['<user>'] = [gh.user().login]
    whois(opts)

@command
def gist(opts):
    """Create a new gist from files"""
    files = {}
    description = opts['<description>'] or ''
    for f in opts['<file>']:
        if f == '-':
            files['stdout'] = {'content': sys.stdin.read()}
        else:
            if not os.path.exists(f):
                err("No such file: %s" % f)
            with open(f) as fd:
                files[os.path.basename(f)] = {'content': fd.read()}
    gist = github().create_gist(description=description, files=files)
    print("Gist created at %s" % gist.html_url)

@command
def gists(opts):
    gh = github()
    user = (opts['<user>'] or [gh.user().login])[0]
    for gist in gh.iter_gists(user):
        print("%s - %s" % (gist.html_url, gist.description))

@command
def add_public_keys(opts):
    """Adds keys to your public keys"""
    if not opts['<key>']:
        opts['<key>'] = glob.glob(os.path.join(os.path.expanduser('~'), '.ssh', 'id_*.pub'))
    gh = github()
    existing = [x.key for x in gh.iter_keys()]
    for arg in opts['<key>']:
        with open(arg) as fd:
            algo, key, title = fd.read().strip().split(None, 2)
        key = "%s %s" % (algo, key)
        if key in existing:
            continue
        print("Adding %s" % arg)
        gh.create_key(title=title, key=key)

@command
def public_keys(opts):
    """Lists all keys for a user"""
    gh = github()
    if gh.user().login == opts['<user>'][0]:
        keys = gh.iter_keys()
    else:
        keys = gh.user(opts['<user>'][0]).iter_keys()
    for key in keys:
        print("%s %s" % (key.key, key.title or ''))

@command
def pull_request(opts):
    """Opens a pull request to merge your branch1 to upstream branch2"""
    repo = get_repo()
    if not repo.fork:
        err("This is not a forked repository")
    parent = repo.parent
    # Which branch?
    src = opts['<branch1:branch2>'] or ''
    dst = None
    if ':' in src:
        src, dst = src.split(':', 1)
    if not src:
        src = check(shell.git('rev-parse', '--abbrev-ref', 'HEAD')).stdout.strip()
    if not dst:
        dst = 'master'

    # Try to get the local commit
    commit = check(shell.git('show-ref', 'refs/heads/%s' % src)).stdout.split()[0]
    # Do they exist on github?
    try:
        srcb = repo.branch(src)
        if srcb.commit.sha != commit:
            err("Branch %s not up to date on github (%s vs %s)" % (src, srcb.commit.sha[:7], commit[:7]))
    except github3.GitHubError:
        err("Branch %s does not exist in your github repo" % src)

    try:
        dstb = parent.branch(dst)
    except github3.GitHubError:
        err("Branch %s does not exist in %s/%s" % (dst, parent.owner.login, parent.name))

    # Do we have the dst locally?
    for remote in check(shell.git('remote')).stdout.strip().split("\n"):
        if check(shell.git('config', 'remote.%s.url' % remote)).stdout.strip() in [parent.git_url, parent.ssh_url, parent.clone_url]:
            break
    else:
        err("You don't have %s/%s configured as a remote repository" % (parent.owner.login, parent.name))

    # How many commits?
    commits = try_decode(check(shell.git('log', '--pretty=%H', '%s/%s..%s' % (remote, dst, src))).stdout).strip().split()
    commits.reverse()
    # 1: title/body from commit
    if not commits:
        err("Your branch has no commits yet")
    # Are we turning an issue into a commit?
    if opts['<issue>']:
        pull = parent.create_pull_from_issue(base=dst, head='%s:%s' % (repo.owner.login, src), issue=int(opts['<issue>']))
        print("Pull request %d created %s" % (pull.number, pull.html_url))
        return
    if len(commits) == 1:
        title, body = check(shell.git('log', '--pretty=%s\n%b', '%s^..%s' % (commits[0], commits[0]))).stdout.split('\n', 1)
        title = title.strip()
        body = body.strip()

    # More: title from branchname (titlecased, s/-/ /g), body comments from shortlog
    else:
        title = src
        if '/' in title:
            title = title[title.rfind('/') + 1:]
        title = title.title().replace('-', ' ')
        body = ""

    body += """
# Requesting a pull from %s/%s into %s/%s
#
# Please enter a message to accompany your pull request. Lines starting
# with '#' will be ignored, and an empty message aborts the commit.
#""" % (repo.owner.login, src, parent.owner.login, dst)
    body += "\n# " + try_decode(check(shell.git('shortlog', '%s/%s..%s' % (remote, dst, src))).stdout).strip().replace('\n', '\n# ')
    body += "\n#\n# " + try_decode(check(shell.git('diff', '--stat', '%s^..%s' % (commits[0], commits[-1]))).stdout).strip().replace('\n', '\n#')
    temp_file = os.path.join(check(shell.git('rev-parse', '--git-dir')).stdout.strip(), 'PULL_REQUEST_EDITMSG')
    with open(temp_file, 'w') as fd:
        fd.write("%s\n\n%s" % (title,body))
    getattr(shell, check(shell.git('var', 'GIT_EDITOR')).stdout.strip())(temp_file, redirect=False)
    with open(temp_file) as fd:
        title, body = (try_decode(fd.read()) +'\n').split('\n', 1)
    title = title.strip()
    body = body.strip()
    body = re.sub('^#.*', '', body, flags=re.MULTILINE).strip()
    if not body:
        err("No pull request message specified")

    pull = parent.create_pull(base=dst, head='%s:%s' % (repo.owner.login, src), title=title, body=body)
    print("Pull request %d created %s" % (pull.number, pull.html_url))

@command
def network(opts):
    """Create a graphviz graph of followers and forks"""
    from collections import defaultdict
    class P:
        def __init__(self, user):
            self.user = user
            self.done = False
            self.rel_to = defaultdict(list)

        def __repr__(self):
            return dict.__repr__(self.rel_to)

    level = 1
    if opts['<level>']:
        try:
            level = int(opts['<level>'])
        except ValueError:
            err("Integer argument required")
    gh = github()
    me = gh.user()
    people = {me.login: P(me)}
    for i in range(level):
        for login, person in list(people.items()):
            if person.done:
                continue

            sys.stderr.write("Looking at user %s" % login)
            # Followers
            for other in person.user.iter_followers():
                if other.login not in people:
                    people[other.login] = P(other)
                people[other.login].rel_to[login].append('follows')
            for other in person.user.iter_following():
                if other.login not in people:
                    people[other.login] = P(other)
                person.rel_to[other.login].append('follows')

            # Forks
            for repo in gh.iter_repos(login, type='owner'):
                sys.stderr.write("Looking at repo %s" % repo.name)
                if repo.fork:
                    # Sigh. GH doesn't return parent info in iter_repos
                    repo = gh.repository(repo.owner.login, repo.name)
                    if repo.owner.login not in people:
                        people[repo.owner.login] = P(repo.owner)
                    person.rel_to[repo.parent.owner.login].append('forked %s' % repo.parent.name)
                else:
                    for fork in repo.iter_forks():
                        if fork.owner.login == login:
                            continue
                        if fork.owner.login not in people:
                            people[fork.owner.login] = P(fork.owner)
                        people[fork.owner.login].rel_to[login].append('forked %s' % repo.name)
            person.done = True

    # Now we create a graph
    graph = ["digraph network {"]
    for person in people:
        graph.append('    "%s"' % person)

    for login, person in people.items():
        for other, types in person.rel_to.items():
            graph.append('    "%s" -> "%s" [label="%s"]' % (login, other, "\\n".join(types)))

    graph.append("}")
    print("\n".join(graph))

@command
def hooks(opts):
    repo = get_repo()
    for hook in repo.iter_hooks():
        print(wrap("%s (%s)" % (hook.name, ', '.join(hook.events)), attr.bright))
        for key, val in sorted(hook.config.items()):
            if val in (None, ''):
                continue
            print("  %s: %s" % (key, val))

@command
def remove_hook(opts):
    repo = get_repo()
    for hook in repo.iter_hooks():
        if hook.name == opts['<name>']:
            hook.delete()

@command
def add_hook(opts):
    repo = get_repo()
    for hook in repo.iter_hooks():
        if hook.name == opts['<name>']:
            raise ValueError("Hook %s already exists" % opts['<name>'])
    settings = dict([x.split('=', 1) for x in opts['<setting>']])
    for key in settings:
        if settings[key].isdigit():
            settings[key] = int(settings[key])
    events = settings.pop('events', 'push').split(',')
    repo.create_hook(opts['<name>'], settings, events)

@command
def edit_hook(opts):
    repo = get_repo()
    for hook in repo.iter_hooks():
        if hook.name == opts['<name>']:
            break
    else:
        raise ValueError("Hook %s does not exist" % opts['<name>'])

    settings = dict([x.split('=', 1) for x in opts['<setting>']])
    for key in settings:
        if settings[key].isdigit():
            settings[key] = int(settings[key])
    events = settings.pop('events', ','.join(hook.events)).split(',')
    config = hook.config
    config.update(settings)
    hook.edit(opts['<name>'], config, events)

@command
def ignore(opts):
    lang = opts['<language>']
    gh = github()
    if not lang:
        langs = sorted(gh.gitignore_templates(), key = lambda x: x.lower())
        print("Languages for which a gitignore template is available:\n  * " + "\n  * ".join(langs))
    else:
        for l in lang:
            print("# Ignore patterns for " + l)
            print(gh.gitignore_template(l).strip())

@command
def browse(opts):
    """Open the GitHub page for this repo in a browser"""
    url = get_repo().html_url
    webbrowser.open_new(url)

main()
