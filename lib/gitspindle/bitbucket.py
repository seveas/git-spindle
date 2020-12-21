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
            user = input("BitBucket user: ").strip()
            self.config('user', user)

        password = self.config('password')
        if not password:
            print("Generate an application password at https://bitbucket.org/account/settings/app-passwords/ and enter it below")
            password = getpass.getpass("BitBucket password: ")
            try:
                bbapi.Bitbucket(user, password).user(user)
            except:
                err("Authentication failed")
            self.config('password', password)
            location = '%s - do not share this file' % self.config_file
            if self.use_credential_helper:
                location = 'git\'s credential helper'
            print("Your BitBucket authentication password is now stored in %s" % location)

        self.bb = bbapi.Bitbucket(user, password)
        self.me = self.bb.user(user)
        self.my_login = self.me.nickname

    def parse_url(self, url):
        return ([self.my_login] + url.path.split('/'))[-2:]

    def get_repo(self, remote, workspace, repo):
        try:
            return self.bb.workspace(workspace).repository(repo)
        except bbapi.BitBucketError:
            pass

    def parent_repo(self, repo):
        if repo.parent:
            return bbapi.Repository(self.bb, url=repo.parent['links']['self']['href'])

    def clone_url(self, repo, opts):
        if opts['--ssh'] or repo.is_private:
            return repo.links['clone']['ssh']
        if opts['--http']:
            return repo.links['clone']['https']
        if repo.owner['nickname'] == self.my_login:
            return repo.links['clone']['ssh']
        return repo.links['clone']['https']

    def api_root(self):
        return 'https://bitbucket.org/api/'

    # Commands
    @command
    def add_deploy_key(self, opts):
        """<key>...
           Add a deploy key"""
        repo = self.repository(opts)
        for arg in opts['<key>']:
            with open(arg) as fd:
                algo, key, label = fd.read().strip().split(None, 2)
            key = "%s %s" % (algo, key)
            print("Adding deploy key %s" % arg)
            repo.add_deploy_key(key, label)

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
        """[--ssh|--http] <user> [<name>]
           Add user's fork as a named remote. The name defaults to the user's loginname"""
        for fork in self.repository(opts).forks():
            if fork.owner['nickname'] in opts['<user>']:
                name = opts['<name>'] or fork.owner['nickname']
                url = self.clone_url(fork, opts)
                self.gitm('remote', 'add', '-f', name, url, redirect=False)

    @command
    @wants_parent
    def apply_pr(self, opts):
        """[--ssh|--http] <pr-number>
           Applies a pull request as a series of cherry-picks"""
        repo = self.repository(opts)
        pr = repo.pull_request(opts['<pr-number>'])
        if not pr:
            err("Pull request %s does not exist" % opts['<pr-number>'])
        print("Applying PR#%d from %s: %s" % (pr.id, pr.author['display_name'] or pr.author['nickname'], pr.title))
        # Warnings
        warned = False
        cbr = self.gitm('rev-parse', '--symbolic-full-name', 'HEAD').stdout.strip().replace('refs/heads/','')
        if cbr != pr.destination['branch']['name']:
            print(wrap("Pull request was filed against %s, but you're on the %s branch" % (pr.destination['branch']['name'], cbr), fgcolor.red))
            warned = True
        if pr.state == 'MERGED':
            print(wrap("Pull request was already merged by %s" % (pr.closed_by['display_name'] or pr.closed_by['nickname']), fgcolor.red))
            warned = True
        if pr.state == 'DECLINED':
            print(wrap("Pull request has already been declined: %s" % pr.reason, fgcolor.red))
            warned = True
        if warned:
            if not self.question("Continue?"):
                sys.exit(1)

        # Fetch PR if needed
        sha = self.git('rev-parse', '--verify', 'refs/pull/%d/head' % pr.id).stdout.strip()
        if not sha.startswith(pr.source['commit']['hash']):
            print("Fetching pull request")
            ws, repo = pr.source['repository']['full_name'].split('/')
            url = self.clone_url(self.bb.workspace(ws).repository(repo), opts)
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
           Open the Bitbucket page for a repository in a browser"""
        sections = ['src', 'commits', 'branches', 'pull-requests', 'downloads', 'admin', 'issues', 'wiki']
        if opts['<repo>'] in sections and not opts['<section>']:
            opts['<repo>'], opts['<section>'] = None, opts['<repo>']
        repo = self.repository(opts)
        url = repo.links['html']['href']
        if opts['<section>']:
            url += '/' + opts['<section>']
        webbrowser.open_new_tab(url)

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
                file = self.rel2root(file)
            try:
                content = repo.src(path=file, revision=ref or 'master') # BitBucket has no API to retrieve the default branch
            except bbapi.BitBucketError:
                err("No such file: %s" % arg)
            if not isinstance(content, bytes):
                err("Not a regular file: %s" % arg)
            os.write(sys.stdout.fileno(), content)

    @command
    def clone(self, opts, repo=None):
        """[--ssh|--http] [--triangular [--upstream-branch=<branch>]] [--parent] [git-clone-options] <repo> [<dir>]
           Clone a repository by name"""
        if not repo:
            repo = self.repository(opts)
        url = self.clone_url(repo, opts)

        args = opts['extra-opts']
        args.append(url)
        dir = opts['<dir>'] and opts['<dir>'][0] or repo.name
        if '--bare' in args:
            dir += '.git'
        args.append(dir)

        self.gitm('clone', *args, redirect=False).returncode
        if repo.parent:
            os.chdir(dir)
            self.set_origin(opts, repo=repo)
            self.gitm('fetch', 'upstream', redirect=False)

    @command
    def create(self, opts):
        """[--private] [--team=<team>] [--description=<description>]
           Create a repository on bitbucket to push to"""
        root = self.gitm('rev-parse', '--show-toplevel').stdout.strip()
        name = os.path.basename(root)
        if opts['--team']:
            dest = self.bb.team(opts['--team'])
        else:
            dest = self.me
        try:
            dest.repository(name)
            err("Repository already exists")
        except bbapi.BitBucketError:
            pass

        repo = dest.create_repository(slug=name, description=opts['--description'], is_private=opts['--private'], has_issues=True, has_wiki=True)
        if 'origin' in self.remotes():
            print("Remote 'origin' already exists, adding the BitBucket repository as 'bitbucket'")
            self.set_origin(opts, repo=repo, remote='bitbucket')
        else:
            self.set_origin(opts, repo=repo)

    @command
    def deploy_keys(self, opts):
        """[<repo>]
           Lists all keys for a repo"""
        repo = self.repository(opts)
        for key in repo.deploy_keys():
            print("%s %s (id: %s)" % (key['key'], key.get('label', ''), key['id']))

    @command
    def fetch(self, opts):
        """[--ssh|--http] <user> [<refspec>]
           Fetch refs from a user's fork"""
        for fork in self.repository(opts).forks():
            if fork.owner['nickname'] in opts['<user>']:
                url = self.clone_url(fork, opts)
                refspec = opts['<refspec>'] or 'refs/heads/*'
                if ':' not in refspec:
                    if not refspec.startswith('refs/'):
                        refspec += ':' + 'refs/remotes/%s/' % fork.owner['nickname'] + refspec
                    else:
                        refspec += ':' + refspec.replace('refs/heads/', 'refs/remotes/%s/' % fork.owner['nickname'])
                self.gitm('fetch', url, refspec, redirect=False)

    @command
    def fork(self, opts):
        """[--ssh|--http] [--triangular [--upstream-branch=<branch>]] [<repo>]
           Fork a repo and clone it"""
        do_clone = bool(opts['<repo>'])
        repo = self.repository(opts)
        if repo.owner['nickname'] == self.my_login:
            err("You cannot fork your own repos")

        try:
            self.me.repository(repo.name)
            err("Repository already exists")
        except bbapi.BitBucketError:
            pass

        my_fork = repo.fork()
        self.wait_for_repo(my_fork.owner['nickname'], my_fork.name, opts)

        if do_clone:
            self.clone(opts, repo=my_fork)
        else:
            self.set_origin(opts, repo=my_fork)

    @command
    @wants_parent
    def forks(self, opts):
        """[<repo>]
           List all forks of this repository"""
        repo = self.repository(opts)
        print("[%s] %s" % (wrap(repo.owner['nickname'], attr.bright), repo.links['html']['href']))
        for fork in repo.forks():
            print("[%s] %s" % (fork.owner['nickname'], fork.links['html']['href']))

    @command
    def issue(self, opts):
        """[<repo>] [--parent] [<issue>...]
           Show issue details or report an issue"""
        if opts['<repo>'] and opts['<repo>'].isdigit():
            # Let's assume it's an issue
            opts['<issue>'].insert(0, opts['<repo>'])
            opts['<repo>'] = None
        repo = self.repository(opts)
        for issue_no in opts['<issue>']:
            try:
                issue = repo.issue(issue_no)
                print(wrap(issue.title.encode(sys.stdout.encoding, errors='backslashreplace').decode(sys.stdout.encoding), attr.bright, attr.underline))
                print(issue.content['raw'].encode(sys.stdout.encoding, errors='backslashreplace').decode(sys.stdout.encoding))
                print(issue.html_url)
            except bbapi.BitBucketError:
                bbe = sys.exc_info()[1]
                if bbe.args[0] == 'No Issue matches the given query.':
                    print('No issue with id %s found in repository %s' % (issue_no, repo.full_name))
                else:
                    raise
        if not opts['<issue>']:
            extra = """Reporting an issue on %s
Please describe the issue as clearly as possible. Lines starting with '#' will
be ignored, the first line will be used as title for the issue.""" % repo.full_name
            title, body = self.edit_msg(None, '', extra, 'ISSUE_EDITMSG')
            if not body:
                err("Empty issue message")
            try:
                issue = repo.create_issue(title=title, body=body)
                print("Issue %d created %s" % (issue.id, issue.html_url))
            except:
                filename = self.backup_message(title, body, 'issue-message-')
                err("Failed to create an issue, the issue text has been saved in %s" % filename)

    @command
    def issues(self, opts):
        """[<repo>] [--parent] [<filter>...]
           List issues in a repository"""
        if opts['<repo>'] and '=' in opts['<repo>']:
            opts['<filter>'].insert(0, opts['<repo>'])
            opts['<repo>'] = None
        if (not opts['<repo>'] and not self.in_repo) or opts['<repo>'] == '--':
            repos = self.me.repositories()
        else:
            repos = [self.repository(opts)]
        for repo in repos:
            if repo.fork and opts['--parent']:
                repo = self.parent_repo(repo) or repo
            filters = dict([x.split('=', 1) for x in opts['<filter>']])
            try:
                issues = repo.issues(**filters)
            except bbapi.BitBucketError:
                issues = None
            try:
                pullrequests = repo.pull_requests()
            except bbapi.BitBucketError:
                pullrequests = None

            if issues:
                print(wrap("Issues for %s" % repo.full_name, attr.bright))
                for issue in issues:
                    print("[%d] %s %s" % (issue.id, issue.title.encode(sys.stdout.encoding, errors='backslashreplace').decode(sys.stdout.encoding), issue.html_url))
            if pullrequests:
                print(wrap("Pull requests for %s" % repo.full_name, attr.bright))
                for pr in pullrequests:
                    print("[%d] %s %s" % (pr.id, pr.title.encode(sys.stdout.encoding, errors='backslashreplace').decode(sys.stdout.encoding), pr.html_url))


    @command
    def ls(self, opts):
        """[<dir>...]
           Display the contents of a directory on BitBucket"""
        for arg in opts['<dir>'] or ['']:
            repo, ref, file = ([None, None] + arg.split(':',2))[-3:]
            user = None
            if repo:
                user, repo = ([None] + repo.split('/'))[-2:]
                repo = self.bb.repository(user or self.my_login, repo)
            else:
                repo = self.repository(opts)
                file = self.rel2root(file)
            try:
                content = repo.src(path=file or '/', revision=ref or 'master') # BitBucket has no API to retrieve the default branch
            except bbapi.BitBucketError:
                err("No such file: %s" % arg)
            if isinstance(content, bytes):
                err("Not a directory: %s" % arg)

            ms = max([len(str(file.get('size', 0))) for file in content])
            content.sort(key=lambda x: x['path'])
            for entry in content:
                print("%*s %s" % (ms, entry.get('size', ''), entry['path']))

    @command
    def mirror(self, opts):
        """[--ssh|--http] [<repo>]
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
            fd.write(repo.description or "")

    @command
    def permissions(self, opts):
        """[<repo>]
           List repo permissions"""
        repo = self.repository(opts)
        order = {'admin': 0, 'write': 1, 'read': 2}
        permissions = repo.permissions()
        if not permissions:
            return
        permissions.sort(key=lambda permission: (order[permission['permission']], permission['user']['nickname']))
        maxlen = max([len(permission['user']['nickname']) for permission in permissions])
        fmt = "%%s %%-%ds (%%s)" % maxlen
        for permission in permissions:
            print(fmt % (wrap("%-5s" % permission['permission'], attr.faint), permission['user']['nickname'], permission['user']['display_name']))

    @command
    def public_keys(self, opts):
        """[<user>]
           Lists all keys for a user"""
        user = opts['<user>'] and self.bb.user(opts['<user>'][0]) or self.me
        for key in user.keys():
            print("%s %s" % (key.key, key.label or ''))

    @command
    def pull_request(self, opts):
        """[--yes] [<yours:theirs>]
           Opens a pull request to merge your branch to an upstream branch"""
        repo = self.repository(opts)
        if repo.parent:
            parent = self.parent_repo(repo)
        else:
            parent = repo
        # Which branch?
        src = opts['<yours:theirs>'] or ''
        dst = None
        if ':' in src:
            src, dst = src.split(':', 1)
        if not src:
            src = self.gitm('rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()
        if not dst:
            dst = parent.mainbranch['name']
            tracking_branch = self.git('rev-parse', '--symbolic-full-name', '%s@{u}' % src).stdout.strip()
            if tracking_branch.startswith('refs/remotes/'):
                tracking_remote, tracking_branch = tracking_branch.split('/', 3)[-2:]
                if tracking_branch != src or repo.remote != tracking_remote:
                    # Interesting. We're not just tracking a branch in our clone!
                    dst = tracking_branch

        if src == dst and parent == repo:
            err("Cannot file a pull request on the same branch")

        # Try to get the local commit
        commit = self.gitm('show-ref', 'refs/heads/%s' % src).stdout.split()[0]
        # Do they exist on bitbucket?
        srcb = repo.branches().get(src, None)
        if not srcb:
            if self.question("Branch %s does not exist in your BitBucket repo, shall I push?" % src):
                self.gitm('push', '-u', repo.remote, src, redirect=False)
                srcb = repo.branches().get(src, None)
            else:
                err("Aborting")
        elif srcb and srcb.target['hash'] != commit:
            # Have we diverged? Then there are commits that are reachable from the bitbucket branch but not local
            diverged = self.gitm('rev-list', srcb.raw_node, '^' + commit)
            if diverged.stderr or diverged.stdout:
                if self.question("Branch %s has diverged from bitbucket, shall I push and overwrite?" % src, default=False):
                    self.gitm('push', '--force', repo.remote, src, redirect=False)
                else:
                    err("Aborting")
            else:
                if self.question("Branch %s not up to date on bitbucket, but can be fast forwarded, shall I push?" % src):
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
        accept_empty_body = False
        commits = self.gitm('log', '--pretty=%H', '%s/%s..%s' % (remote, dst, src)).stdout.strip().split()
        commits.reverse()
        if not commits:
            err("Your branch has no commits yet")

        # 1 commit: title/body from commit
        if len(commits) == 1:
            title, body = self.gitm('log', '--pretty=%s\n%b', '%s^..%s' % (commits[0], commits[0])).stdout.split('\n', 1)
            title = title.strip()
            body = body.strip()
            accept_empty_body = not bool(body)

        # More commits: title from branchname (titlecased, s/-/ /g), body comments from shortlog
        else:
            title = src
            if '/' in title:
                title = title[title.rfind('/') + 1:]
            title = title.title().replace('-', ' ')
            body = ""

        extra = """Requesting a pull from %s/%s into %s/%s

Please enter a message to accompany your pull request. Lines starting
with '#' will be ignored, and an empty message aborts the request.""" % (repo.owner['nickname'], src, parent.owner['nickname'], dst)
        extra += "\n\n" + self.gitm('shortlog', '%s/%s..%s' % (remote, dst, src)).stdout.strip()
        extra += "\n\n" + self.gitm('diff', '--stat', '%s^..%s' % (commits[0], commits[-1])).stdout.strip()
        title, body = self.edit_msg(title, body, extra, 'PULL_REQUEST_EDIT_MSG')
        if not body and not accept_empty_body:
            err("No pull request message specified")

        try:
            pull = parent.create_pull_request(src=srcb, dst=dstb, title=title, body=body)
            print("Pull request %d created %s" % (pull.id, pull.links['html']['href']))
        except:
            filename = self.backup_message(title, body, 'pull-request-message-')
            err("Failed to create a pull request, the pull request text has been saved in %s" % filename)

    @command
    def remove_deploy_key(self, opts):
        """<key>...
           Remove deploy key by id"""
        repo = self.repository(opts)
        for key in opts['<key>']:
            repo.remove_deploy_key(key)

    @command
    def repos(self, opts):
        """[--no-forks] [<workspace>]
           List all repos of a workspace, or your repos"""
        if opts['<workspace>']:
            repos = self.bb.workspace(opts['<workspace>']).repositories()
        else:
            repos = self.me.repositories()
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
            print(wrap(fmt % (repo.full_name, '(%s)' % repo.scm, repo.description), *color))

    @command
    def set_origin(self, opts, repo=None, remote='origin'):
        """[--ssh|--http] [--triangular [--upstream-branch=<branch>]]
           Set the remote 'origin' to bitbucket.
           If this is a fork, set the remote 'upstream' to the parent"""
        if not repo:
            repo = self.repository(opts)
            # Is this mine? No? Do I have a clone?
            if repo.owner['nickname'] != self.my_login:
                try:
                    repo = self.me.repository(repo.slug)
                except bbapi.BitBucketError:
                    pass

        url = self.clone_url(repo, opts)
        if self.git('config', 'remote.%s.url' % remote).stdout.strip() != url:
            print("Pointing %s to %s" % (remote, url))
            self.gitm('config', 'remote.%s.url' % remote, url)
        self.gitm('config', '--replace-all', 'remote.%s.fetch' % remote, '+refs/heads/*:refs/remotes/%s/*' % remote)

        if repo.parent:
            parent = self.parent_repo(repo)
            url = self.clone_url(parent, opts)
            if self.git('config', 'remote.upstream.url').stdout.strip() != url:
                print("Pointing upstream to %s" % url)
                self.gitm('config', 'remote.upstream.url', url)
            self.gitm('config', 'remote.upstream.fetch', '+refs/heads/*:refs/remotes/upstream/*')

        if self.git('ls-remote', remote).stdout.strip():
            self.gitm('fetch', remote, redirect=False)
        if repo.parent:
            self.gitm('fetch', 'upstream', redirect=False)

        if remote != 'origin':
            return

        self.set_tracking_branches(remote, upstream="upstream", triangular=opts['--triangular'], upstream_branch=opts['--upstream-branch'])

    @command
    def snippet(self, opts):
        """[--description=<description>] <file>...
           Create a new snippet from files or stdin"""
        files = {}
        description = opts['--description'] or ''
        for f in opts['<file>']:
            if f == '-':
                files['stdout'] = sys.stdin.read()
            else:
                if not os.path.exists(f):
                    err("No such file: %s" % f)
                with open(f) as fd:
                    files[os.path.basename(f)] = fd.read()
        snippet = self.me.create_snippet(description=description, files=files)
        print("Snippet created at %s" % snippet.links['html']['href'])

    @command
    def snippets(self, opts):
        """[<user>]
           Show all snippets for a user"""
        snippets = self.bb.user(opts['<user>'] or self.my_login).snippets()
        for snippet in snippets:
            print("%s - %s" % (snippet.title, snippet.links['html']['href']))

    @command
    def whoami(self, opts):
        """\nDisplay BitBucket user info"""
        opts['<user>'] = [self.my_login]
        self.whois(opts)

    @command
    def whois(self, opts):
        """<user>...
           Display Bitbucket user info"""
        for user_ in opts['<user>']:
            user = self.bb.user(user_)
            if not user:
                print("No such user: %s" % user_)
                continue
            print(wrap(user.display_name or user.nickname, attr.bright, attr.underline))
            print("UUID:     %s" % user.account_id)
            print("Profile:  %s" % user.links['html']['href'])
            if user.location:
                print("Location: %s" % user.location)
            try:
                keys = user.keys()
            except bbapi.BitBucketError:
                keys = []
            for pkey in keys:
                algo, key = pkey.key.split()[:2]
                algo = algo[4:].upper()
                if pkey.label:
                    print("%s key%s...%s (%s)" % (algo, ' ' * (6 - len(algo)), key[-10:], pkey.label))
                else:
                    print("%s key%s...%s" % (algo, ' ' * (6 - len(algo)), key[-10:]))
