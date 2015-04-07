from gitspindle import *
from gitspindle.ansi import *
import gitspindle.bbapi as bbapi
import getpass
import glob
import os
import sys
import webbrowser
import binascii

class BitBucket(GitSpindle):
    prog = 'git bucket'
    what = 'BitBucket'
    spindle = 'bitbucket'
    hosts = ['bitbucket.org', 'www.bitbucket.org']
    api = bbapi

    # Support functions
    def login(self):
        user = self.config('user')
        if not user:
            user = raw_input("BitBucket user: ").strip()
            self.config('user', user)

        password = self.config('password')
        if not password:
            password = getpass.getpass("BitBucket password: ")
            try:
                bbapi.Bitbucket(user, password).user(user)
            except:
                err("Authentication failed")
            self.config('password', password)
            print("Your BitBucket authentication password is now cached in %s - do not share this file" % self.config_file)

        self.bb = bbapi.Bitbucket(user, password)
        self.me = self.bb.user(user)
        self.my_login = self.me.username

    def parse_url(self, url):
        return ([self.my_login] + url.path.split('/'))[-2:]

    def get_repo(self, remote, user, repo):
        try:
            return self.bb.repository(user, repo)
        except bbapi.BitBucketError:
            pass

    def parent_repo(self, repo):
        if getattr(repo, 'is_fork', None):
            return self.bb.repository(repo.fork_of['owner'], repo.fork_of['slug'])

    def clone_url(self, repo, opts):
        if opts['--ssh'] or repo.is_private:
            return repo.links['clone']['ssh']
        if opts['--http']:
            return repo.links['clone']['https']
        if repo.owner['username'] == self.my_login:
            return repo.links['clone']['ssh']
        return repo.links['clone']['https']

    # Commands
    @command
    def add_public_keys(self, opts):
        """[<key>...]
           Adds keys to your public keys"""
        if not opts['<key>']:
            opts['<key>'] = glob.glob(os.path.join(os.path.expanduser('~'), '.ssh', 'id_*.pub'))
        existing = [x.key for x in self.me.keys()]
        for arg in opts['<key>']:
            with open(arg) as fd:
                algo, key, title = fd.read().strip().split(None, 2)
            key = "%s %s" % (algo, key)
            if key in existing:
                continue
            print("Adding %s" % arg)
            self.me.create_key(label=title, key=key)

    @command
    @wants_parent
    def add_remote(self, opts):
        """[--ssh|--http] <user>...
           Add user's fork as a remote by that name"""
        for fork in self.repository(opts).forks():
            if fork.owner['username'] in opts['<user>']:
                url = self.clone_url(fork, opts)
                self.gitm('remote', 'add', fork.owner['username'], url)
                self.gitm('fetch', fork.owner['username'], redirect=False)

    @command
    @wants_parent
    def apply_pr(self, opts):
        """<pr-number>
           Applies a pull request as a series of cherry-picks"""
        repo = self.repository(opts)
        pr = repo.pull_request(opts['<pr-number>'])
        if not pr:
            err("Pull request %s does not exist" % opts['<pr-number>'])
        pprint(pr.data)
        print("Applying PR#%d from %s: %s" % (pr.id, pr.author['display_name'] or pr.author['username'], pr.title))
        # Warnings
        warned = False
        cbr = self.gitm('rev-parse', '--symbolic-full-name', 'HEAD').stdout.strip().replace('refs/heads/','')
        if cbr != pr.destination['branch']['name']:
            print(wrap("Pull request was filed against %s, but you're on the %s branch" % (pr.destination['branch']['name'], cbr), fgcolor.red))
            warned = True
        if pr.state == 'MERGED':
            print(wrap("Pull request was already merged by %s" % (pr.closed_by['display_name'] or pr.closed_by['username']), fgcolor.red))
            warned = True
        if pr.state == 'DECLINED':
            print(wrap("Pull request has already been declined: %s" % pr.reason, fgcolor.red))
            warned = True
        if warned:
            if raw_input("Continue? [y/N] ") not in ['y', 'Y']:
                sys.exit(1)

        # Fetch PR if needed
        sha = self.git('rev-parse', '--verify', 'refs/pull/%d/head' % pr.id).stdout.strip()
        if not sha.startswith(pr.source['commit']['hash']):
            print("Fetching pull request")
            url = self.bb.repository(*pr.source['repository']['full_name'].split('/')).links['clone']['https']
            self.gitm('fetch', url, 'refs/heads/%s:refs/pull/%d/head' % (pr.source['branch']['name'], pr.id), redirect=False)
        head_sha = self.gitm('rev-parse', 'HEAD').stdout.strip()
        if self.git('merge-base', pr.source['commit']['hash'], head_sha).stdout.strip() == head_sha:
            print("Fast-forward merging %s..refs/pull/%d/head" % (pr.destination['branch']['name'], pr.id))
            self.gitm('merge', '--ff-only', 'refs/pull/%d/head' % pr.id, redirect=False)
        else:
            print("Cherry-picking  %s..refs/pull/%d/head" % (pr.destination['branch']['name'], pr.id))
            self.gitm('cherry-pick', '%s..refs/pull/%d/head' % (pr.destination['branch']['name'], pr.id), redirect=False)

    @command
    def browse(self, opts):
        """[--parent] [<repo>] [<section>]
           Open the GitHub page for a repository in a browser"""
        sections = ['src', 'commits', 'branches', 'pull-requests', 'downloads', 'admin', 'issues', 'wiki']
        if opts['<repo>'] in sections and not opts['<section>']:
            opts['<repo>'], opts['<section>'] = None, opts['<repo>']
        repo = self.repository(opts)
        url = repo.links['html']['href']
        if opts['<section>']:
            url += '/' + opts['<section>']
        webbrowser.open_new(url)

    @command
    def cat(self, opts):
        """<file>...
           Display the contents of a file on BitBucket"""
        for arg in opts['<file>']:
            repo, ref, file = ([None, None] + arg.split(':',2))[-3:]
            user = None
            if repo:
                user, repo = ([None] + repo.split('/'))[-2:]
                repo = self.bb.repository(user or self.my_login, repo)
            else:
                repo = self.repository(opts)
            try:
                content = repo.src(path=file, revision=ref)
            except bbapi.BitBucketError:
                err("No such file: %s" % arg)
            if not hasattr(content, '_data'):
                err("Not a regular file: %s" % arg)
            if getattr(content, 'encoding', None) == 'base64':
                os.write(sys.stdout.fileno(), binascii.a2b_base64(content._data))
            else:
                print(content._data)

    @command
    def clone(self, opts):
        """[--ssh|--http] [--parent] [git-clone-options] <repo> [<dir>]
           Clone a repository by name"""
        repo = self.repository(opts)
        url = self.clone_url(repo, opts)

        args = opts['extra-opts']
        args.append(url)
        dir = opts['<dir>'] and opts['<dir>'][0] or repo.name
        if '--bare' in args:
            dir += '.git'
        args.append(dir)

        self.gitm('clone', *args, redirect=False).returncode
        if repo.is_fork:
            os.chdir(dir)
            self.set_origin(opts)
            self.gitm('fetch', 'upstream', redirect=False)

    @command
    def create(self, opts):
        """[--private] [-d <description>]
           Create a repository on bitbucket to push to"""
        root = self.gitm('rev-parse', '--show-toplevel').stdout.strip()
        name = os.path.basename(root)
        try:
            self.me.repository(name)
            err("Repository already exists")
        except bbapi.BitBucketError:
            pass

        self.me.create_repository(slug=name, description=opts['-d'], is_private=opts['--private'])
        if 'origin' in self.remotes():
            print("Remote 'origin' already exists, adding the BitBucket repository as 'bitbucket'")
            self.set_origin(opts, 'bitbucket')
        else:
            self.set_origin(opts)

    @command
    def fork(self, opts):
        """[--ssh|--http] [<repo>]
           Fork a repo and clone it"""
        do_clone = bool(opts['<repo>'])
        repo = self.repository(opts)
        if repo.owner['username'] == self.my_login:
            err("You cannot fork your own repos")

        try:
            self.me.repository(repo.name)
            err("Repository already exists")
        except bbapi.BitBucketError:
            pass

        opts['<repo>'] = repo.fork().name

        if do_clone:
            self.clone(opts)
        else:
            self.set_origin(opts)

    @command
    @wants_parent
    def forks(self, opts):
        """[<repo>]
           List all forks of this repository"""
        repo = self.repository(opts)
        print("[%s] %s" % (wrap(repo.owner['username'], attr.bright), repo.links['html']['href']))
        for fork in repo.forks():
            print("[%s] %s" % (fork.owner['username'], fork.links['html']['href']))

    @command
    def issue(self, opts):
        """[<repo>] [--parent] [<issue>...]
           Show issue details or report an issue"""
        if opts['<repo>'] and opts['<repo>'].isdigit():
            # Let's assume it's an issue
            opts['<issue>'].insert(0, opts['<repo>'])
        repo = self.repository(opts)
        for issue in opts['<issue>']:
            issue = repo.issue(issue)
            print(wrap(issue.title, attr.bright, attr.underline))
            print(issue.content)
            print(issue.html_url)
        if not opts['<issue>']:
            body = """
# Reporting an issue on %s/%s
# Please describe the issue as clarly as possible. Lines starting with '#' will
# be ignored, the first line will be used as title for the issue.
#""" % (repo.owner['username'], repo.name)
            title, body = self.edit_msg(body, 'ISSUE_EDITMSG')
            if not body:
                err("Empty issue message")

            issue = repo.create_issue(title=title, body=body)
            print("Issue %d created %s" % (issue.local_id, issue.html_url))

    @command
    def issues(self, opts):
        """[<repo>] [--parent] [<filter>...]
           List issues in a repository"""
        repo = self.repository(opts)
        if not repo:
            repos = self.me.repositories()
        else:
            repos = [repo]
        for repo in repos:
            if repo.fork and opts['--parent']:
                repo = self.parent_repo(repo) or repo
            filters = dict([x.split('=', 1) for x in opts['<filter>']])
            try:
                issues = repo.issues(**filters)
            except bbapi.BitBucketError:
                continue
            print(wrap("Issues for %s" % repo.full_name, attr.bright))
            for issue in issues:
                print("[%d] %s https://bitbucket.org/%s/issue/%d/" % (issue.local_id, issue.title, repo.full_name, issue.local_id))

    @command
    def ls(self, opts):
        """<dir>...
           Display the contents of a directory on BitBucket"""
        for arg in opts['<dir>']:
            repo, ref, file = ([None, None] + arg.split(':',2))[-3:]
            user = None
            if repo:
                user, repo = ([None] + repo.split('/'))[-2:]
                repo = self.bb.repository(user or self.my_login, repo)
            else:
                repo = self.repository(opts)
            try:
                content = repo.src(path=file, revision=ref)
            except bbapi.BitBucketError:
                err("No such file: %s" % arg)
            if hasattr(content, '_data'):
                err("Not a directory: %s" % arg)
            content = content.files + [{'path': x, 'size': 0, 'revision': '', 'type': 'dir'} for x in content.directories]
            content.sort(key=lambda x: x['path'])
            mt = max([len(file.get(type, 'file')) for file in content])
            ms = max([len(str(file['size'])) for file in content])
            fmt = "%%(type)-%ds %%(size)-%ds %%(revision)7.7s %%(path)s" % (mt, ms)
            for file in content:
                if 'type' not in file:
                    file['type'] = 'file'
                print(fmt % file)

    @command
    def mirror(self, opts):
        """[--ssh|--http] [--goblet] [<repo>]
           Mirror a repository, or all repositories for a user"""
        if opts['<repo>'] and opts['<repo>'].endswith('/*'):
            user = opts['<repo>'].rsplit('/', 2)[-2]
            for repo in self.bb.user(user).repositories():
                opts['<repo>'] = repo.full_name
                self.mirror(opts)
            return
        repo = self.repository(opts)
        git_dir = repo.name + '.git'
        cur_dir = os.path.basename(os.path.abspath(os.getcwd()))
        if cur_dir != git_dir and not os.path.exists(git_dir):
            url = self.clone_url(repo, opts)
            self.gitm('clone', '--mirror', url, git_dir, redirect=False)
        else:
            if git_dir == cur_dir:
                git_dir = '.'
            # Update the current, mirrored repo
            if self.git('--git-dir', git_dir, 'config', 'core.bare').stdout.strip() != 'true' or \
               self.git('--git-dir', git_dir, 'config', 'remote.origin.mirror').stdout.strip() != 'true':
                   err("This is not a mirrored repository")
            self.gitm('--git-dir', git_dir, 'fetch', '-q', '--prune', 'origin', redirect=False)

        with open(os.path.join(git_dir, 'description'), 'w') as fd:
            if PY3:
                fd.write(repo.description or "")
            else:
                fd.write((repo.description or "").encode('utf-8'))
        if opts['--goblet']:
            if repo.is_fork:
                owner = self.parent_repo(repo).owner
                owner = owner['display_name'] or owner['username']
            else:
                owner = repo.owner['display_name'] or repo.owner['username']
            self.gitm('--git-dir', git_dir, 'config', 'goblet.owner', owner.encode('utf-8'))
            self.gitm('--git-dir', git_dir, 'config', 'goblet.cloneurlhttp', repo.links['clone']['https'])
            goblet_dir = os.path.join(git_dir, 'goblet')
            if not os.path.exists(goblet_dir):
                os.mkdir(goblet_dir, 0o777)
                os.chmod(goblet_dir, 0o777)

    @command
    def public_keys(self, opts):
        """[<user>]
           Lists all keys for a user"""
        user = opts['<user>'] and self.bb.user(opts['<user>'][0]) or self.me
        for key in user.keys():
            print("%s %s" % (key.key, key.label or ''))

    @command
    def pull_request(self, opts):
        """[<branch1:branch2>]
           Opens a pull request to merge your branch1 to upstream branch2"""
        repo = self.repository(opts)
        if repo.is_fork:
            parent = self.parent_repo(repo)
        else:
            parent = repo
        # Which branch?
        src = opts['<branch1:branch2>'] or ''
        dst = None
        if ':' in src:
            src, dst = src.split(':', 1)
        if not src:
            src = self.gitm('rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()
        if not dst:
            dst = parent.main_branch()

        if src == dst and parent == repo:
            err("Cannot file a pull request on the same branch")

        # Try to get the local commit
        commit = self.gitm('show-ref', 'refs/heads/%s' % src).stdout.split()[0]
        # Do they exist on bitbucket?
        srcb = repo.branches().get(src, None)
        if not srcb:
            if raw_input("Branch %s does not exist in your BitBucket repo, shall I push? [Y/n] " % src).lower() in ['y', 'Y', '']:
                self.gitm('push', repo.remote, src, redirect=False)
                srcb = repo.branches().get(src, None)
            else:
                err("Aborting")
        elif srcb and srcb.raw_node != commit:
            # Have we diverged? Then there are commits that are reachable from the github branch but not local
            diverged = self.gitm('rev-list', srcb.raw_node, '^' + commit)
            if diverged.stderr or diverged.stdout:
                if raw_input("Branch %s has diverged from github, shall I push and overwrite? [y/N] " % src) in ['y', 'Y']:
                    self.gitm('push', '--force', repo.remote, src, redirect=False)
                else:
                    err("Aborting")
            else:
                if raw_input("Branch %s not up to date on github, but can be fast forwarded, shall I push? [Y/n] " % src) in ['y', 'Y', '']:
                    self.gitm('push', repo.remote, src, redirect=False)
                else:
                    err("Aborting")
            srcb = repo.branches().get(src, None)

        dstb = parent.branches().get(dst, None)
        if not dstb:
            err("Branch %s does not exist in %s/%s" % (dst, parent.owner.login, parent.name))

        # Do we have the dst locally?
        for remote in self.gitm('remote').stdout.strip().split("\n"):
            url = self.gitm('config', 'remote.%s.url' % remote).stdout.strip()
            if url in parent.links['clone'].values():
                if parent.is_private and url != parent.links['clone']['ssh']:
                    err("You should configure %s to fetch via ssh, it is a private repo" % parent.full_name)
                self.gitm('fetch', remote, redirect=False)
                break
        else:
            err("You don't have %ss configured as a remote repository" % parent.full_name)

        # How many commits?
        commits = try_decode(self.gitm('log', '--pretty=%H', '%s/%s..%s' % (remote, dst, src)).stdout).strip().split()
        commits.reverse()
        # 1: title/body from commit
        if not commits:
            err("Your branch has no commits yet")
        if len(commits) == 1:
            title, body = self.gitm('log', '--pretty=%s\n%b', '%s^..%s' % (commits[0], commits[0])).stdout.split('\n', 1)
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
# with '#' will be ignored, and an empty message aborts the request.
#""" % (repo.owner['username'], src, parent.owner['username'], dst)
        body += "\n# " + try_decode(self.gitm('shortlog', '%s/%s..%s' % (remote, dst, src)).stdout).strip().replace('\n', '\n# ')
        body += "\n#\n# " + try_decode(self.gitm('diff', '--stat', '%s^..%s' % (commits[0], commits[-1])).stdout).strip().replace('\n', '\n#')
        title, body = self.edit_msg("%s\n\n%s" % (title,body), 'PULL_REQUEST_EDIT_MSG')
        if not body:
            err("No pull request message specified")

        pull = parent.create_pull_request(src=srcb, dst=dstb, title=title, body=body)
        print("Pull request %d created %s" % (pull.id, pull.links['html']['href']))

    @command
    def repos(self, opts):
        """[--no-forks] [<user>]
           List all repos of a user, by default yours"""
        repos = self.bb.user(opts['<user>'] or self.my_login).repositories()
        if not repos:
            return
        maxlen = max([len(x.name) for x in repos])
        fmt = u"%%-%ds %%5s %%s" % maxlen
        for repo in repos:
            color = [attr.normal]
            if repo.is_private:
                color.append(fgcolor.red)
            if 'parent' in repo.data:
                if opts['--no-forks']:
                    continue
                color.append(attr.faint)
            print(wrap(fmt % (repo.name, '(%s)' % repo.scm, repo.description), *color))

    @command
    def set_origin(self, opts, remote='origin'):
        """[--ssh|--http]
           Set the remote 'origin' to github.
           If this is a fork, set the remote 'upstream' to the parent"""
        repo = self.repository(opts)
        # Is this mine? No? Do I have a clone?
        if repo.owner['username'] != self.my_login:
            try:
                repo = self.me.repository(repo.slug)
            except bbapi.BitBucketError:
                pass

        url = self.clone_url(repo, opts)
        if self.git('config', 'remote.%s.url' % remote).stdout.strip() != url:
            print("Pointing %s to %s" % (remote, url))
            self.gitm('config', 'remote.%s.url' % remote, url)
        self.gitm('config', '--replace-all', 'remote.%s.fetch' % remote, '+refs/heads/*:refs/remotes/origin/*')

        if repo.is_fork:
            parent = self.bb.repository(repo.fork_of['owner'], repo.fork_of['slug'])
            url = self.clone_url(parent, opts)
            if self.git('config', 'remote.upstream.url').stdout.strip() != url:
                print("Pointing upstream to %s" % url)
                self.gitm('config', 'remote.upstream.url', url)
            self.gitm('config', 'remote.upstream.fetch', '+refs/heads/*:refs/remotes/upstream/*')

        if self.git('ls-remote', remote).stdout.strip():
            self.gitm('fetch', remote, redirect=False)
        if repo.is_fork:
            self.gitm('fetch', 'upstream', redirect=False)

        if remote != 'origin':
            return

        for branch in self.git('for-each-ref', 'refs/heads/**').stdout.strip().splitlines():
            branch = branch.split(None, 2)[-1][11:]
            if self.git('for-each-ref', 'refs/remotes/origin/%s' % branch).stdout.strip():
                if self.git('config', 'branch.%s.remote' % branch).returncode != 0:
                    print("Marking %s as remote-tracking branch" % branch)
                    self.gitm('config', 'branch.%s.remote' % branch, 'origin')
                    self.gitm('config', 'branch.%s.merge' % branch, 'refs/heads/%s' % branch)

    @command
    def whoami(self, opts):
        """\nDisplay BitBucket user info"""
        opts['<user>'] = [self.my_login]
        self.whois(opts)

    @command
    def whois(self, opts):
        """<user>...
           Display GitHub user info"""
        for user_ in opts['<user>']:
            user = self.bb.user(user_)
            if not user:
                print("No such user: %s" % user_)
                continue
            print(wrap(user.display_name or user.username, attr.bright, attr.underline))
            print("Profile:  %s" % user.links['html']['href'])
            if user.website:
                print("Website:  %s" % user.website)
            if user.location:
                print("Location: %s" % user.location)
            try:
                keys = user.keys()
            except bbapi.BitBucketError:
                keys = []
            for pkey in keys:
                algo, key = pkey.key.split()
                algo = algo[4:].upper()
                if pkey.label:
                    print("%s key%s...%s (%s)" % (algo, ' ' * (6 - len(algo)), key[-10:], pkey.label))
                else:
                    print("%s key%s...%s" % (algo, ' ' * (6 - len(algo)), key[-10:]))
