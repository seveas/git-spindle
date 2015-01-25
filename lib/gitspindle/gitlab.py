from gitspindle import *
from gitspindle.ansi import *
import gitspindle.glapi as glapi
import base64
import datetime
import getpass
import os
import sys
import webbrowser

hidden_command = lambda fnc: os.getenv('DEBUG') and command(fnc)

class GitLab(GitSpindle):
    prog = 'git lab'
    what = 'GitLab'
    spindle = 'gitlab'

    def __init__(self):
        super(GitLab, self).__init__()
        self.gl = self.gitlab()

    # Support functions
    def gitlab(self):
        gl = None
        user = self.config('gitlab.user')
        if not user:
            user = raw_input("GitLab user: ").strip()
            self.config('gitlab.user', user)

        token = self.config('gitlab.token')
        if not token:
            password = getpass.getpass("GitLab password: ")
            gl = glapi.Gitlab('https://gitlab.com/', email=user, password=password)
            gl.auth()
            token = gl.user.private_token
            self.config('gitlab.token', token)
            print("Your GitLab authentication token is now cached in ~/.gitspindle - do not share this file")

        if not user or not token:
            err("No user or token specified")

        if not gl:
            gl = glapi.Gitlab('https://gitlab.com', email=user, private_token=token)
            try:
                gl.auth()
            except glapi.GitlabAuthenticationError:
                # Token obsolete
                self.gitm('config', '--file', self.config_file, '--unset', 'gitlab.token')
                return self.gitlab()
        self.me = gl.user
        return gl

    def parse_repo(self, remote, repo):
        if remote:
            id = self.git('config', 'remote.%s.gitlab-id' % remote).stdout.strip()
            if id and id.isdigit():
                return self.gl.Project(id)

        if '@' in repo:
            repo = repo[repo.find('@')+1:]
        if ':' in repo:
            repo = repo[repo.find(':')+1:]

        if '/' in repo:
            user, repo = repo.rsplit('/',2)[-2:]
        else:
            user, repo = self.me.username, repo

        if repo.endswith('.git'):
            repo = repo[:-4]

        repo_ = self.find_repo(user=user, name=repo)
        if not repo_:
            # Name and path don't always match, and we clone using the name
            repo_ = self.find_repo(user, name=os.path.basename(os.getcwd()))
        if repo_ and remote:
            self.gitm('config', 'remote.%s.gitlab-id' % remote, repo_.id)
        return repo_

    def clone_url(self, repo, opts):
        if opts['--ssh'] or not repo.public:
            return repo.ssh_url_to_repo
        if opts['--http']:
            return repo.http_url_ro_repo
        if repo.owner.username == self.me.username:
            return repo.ssh_url_to_repo
        return repo.http_url_to_repo

    def parent_repo(self, repo):
       if getattr(repo, 'forked_from_project', False):
           return self.gl.Project(repo.forked_from_project['id'])

    # There's no way to fetch a repo by name. Abuse search.
    def find_repo(self, user, name):
        luser = user.lower()
        lname = name.lower()
        try:
            for repo in self.gl.search_projects(name, per_page=100):
                if lname in (repo.name.lower(), repo.path.lower()) and luser in (repo.namespace.name.lower(), repo.namespace.path.lower()):
                    return repo
        except glapi.GitlabListError:
            pass

    # There's no way to fetch a user by username. Abuse seaarch.
    def find_user(self, username):
        try:
            for user in self.gl.User(search=username):
                if user.username == username:
                    return user
        except glapi.GitlabListError:
            pass

    def profile_url(self, user):
        return 'https://gitlab.com/u/%s' % user.username

    def issue_url(self, issue):
        repo = self.gl.Project(issue.project_id)
        return '%s/issues/%d' % (repo.web_url, issue.iid)

    def merge_url(self, merge):
        repo = self.gl.Project(merge.project_id)
        return '%s/merge_requests/%d' % (repo.web_url, merge.iid)

    # commands

    @command
    def add_public_keys(self, opts):
        """[<key>...]
           Adds keys to your public keys"""
        if not opts['<key>']:
            opts['<key>'] = glob.glob(os.path.join(os.path.expanduser('~'), '.ssh', 'id_*.pub'))
        existing = [x.key for x in self.me.Key()]
        for arg in opts['<key>']:
            with open(arg) as fd:
                algo, key, title = fd.read().strip().split(None, 2)
            key = "%s %s" % (algo, key)
            if key in existing:
                continue
            print("Adding %s" % arg)
            glapi.CurrentUserKey(self.gl, {'title': title, 'key': key}).save()

    @command
    @needs_repo
    def add_remote(self, opts):
        """[--ssh|--http] <user>...
           Add user's fork as a remote by that name"""
        dwim = opts['remotes']['.dwim']
        for user in opts['<user>']:
            repo = self.find_repo(user, dwim.name)
            if not repo:
                err("Repository %s/%s does not exist" % (user, dwim.name))
            url = self.clone_url(repo, opts)
            self.gitm('remote', 'add', user, url)
            self.gitm('config', 'remote.%s.gitlab-id' % user, repo.id)
            self.gitm('fetch', user, redirect=False)

    @command
    @needs_repo
    def apply_merge(self, opts):
        """<merge-request-number>
           Applies a merge request as a series of cherry-picks"""
        repo = opts['remotes']['.dwim']
        mn = int(opts['<merge-request-number>'])
        for req in repo.MergeRequest():
            if req.iid == mn:
                mr = req
                break
        else:
            err("Merge request %s does not exist" % opts['<merge-request-number>'])
        print("Applying merge request #%d from %s: %s" % (mr.iid, mr.author.name, mr.title))
        # Warnings
        warned = False
        cbr = self.gitm('rev-parse', '--symbolic-full-name', 'HEAD').stdout.strip().replace('refs/heads/','')
        if cbr != mr.target_branch:
            print(wrap("Merge request was filed against %s, but you're on the %s branch" % (mr.base.ref, cbr), fgcolor.red))
            warned = True
        if mr.state == 'merged':
            print(wrap("Merge request was already merged", fgcolor.red))
        if mr.state == 'closed':
            print(wrap("Merge request has already been closed", fgcolor.red))
            warned = True
        if warned:
            if raw_input("Continue? [y/N] ") not in ['y', 'Y']:
                sys.exit(1)
        # Fetch mr if needed
        sha = self.git('rev-parse', '--verify', 'refs/merge/%d/head' % mr.iid).stdout.strip()
        if not sha:
            print("Fetching merge request")
            url = glapi.Project(self.gl, mr.source_project_id).http_url_to_repo
            self.gitm('fetch', url, 'refs/heads/%s:refs/merge/%d/head' % (mr.source_branch, mr.iid), redirect=False)
        head_sha = self.gitm('rev-parse', 'HEAD').stdout.strip()
        if self.git('merge-base', 'refs/merge/%d/head' % mr.iid, head_sha).stdout.strip() == head_sha:
            print("Fast-forward merging %s..refs/merge/%d/head" % (mr.target_branch, mr.iid))
            self.gitm('merge', '--ff-only', 'refs/merge/%d/head' % mr.iid, redirect=False)
        else:
            print("Cherry-picking %s..refs/merge/%d/head" % (mr.target_branch, mr.iid))
            self.gitm('cherry-pick', '%s..refs/merge/%d/head' % (mr.target_branch, mr.iid), redirect=False)

    @command
    def browse(self, opts):
        """[--parent] [<repo>] [<section>]
           Open the GitLab page for a repository in a browser"""
        sections = ['issues', 'merge_requests', 'wiki', 'files', 'commits', 'branches', 'graphs', 'settings']
        if opts['<repo>'] in sections and not opts['<section>']:
            opts['<repo>'], opts['<section>'] = None, opts['<repo>']
        repo = self.get_remotes(opts)['.dwim']
        section_map = {'wiki': 'wikis/home', 'files': 'tree/%s' % repo.default_branch,
                       'commits': 'commits/%s' % repo.default_branch, 'settings': 'edit',
                       'graphs': 'graphs/%s' % repo.default_branch}
        url = repo.web_url
        if opts['<section>']:
            url += '/' + section_map.get(opts['<section>'], opts['<section>'])
        webbrowser.open_new(url)

    @command
    def cat(self, opts):
        """<file>...
           Display the contents of a file on github"""
        for file in opts['<file>']:
            repo, ref, file = ([None, None] + file.split(':',2))[-3:]
            user = None
            if repo:
                user, repo = ([None] + repo.split('/'))[-2:]
                repo = self.find_repo(user or self.me.username, repo)
            else:
                repo = self.get_remotes(opts)['.dwim']

            try:
                file = repo.File(ref=ref or repo.default_branch, file_path=file)
                os.write(sys.stdout.fileno(), base64.b64decode(file.content))
            except glapi.GitlabGetError:
                sys.stderr.write("No such file: %s\n" % file)

    @command
    def clone(self, opts):
        """[--ssh|--http] [--parent] [git-clone-options] <repo> [<dir>]
           Clone a repository by name"""
        repo = opts['remotes']['.dwim']
        url = self.clone_url(repo, opts)

        args = opts['extra-opts']
        args.append(url)
        dir = opts['<dir>'] or repo.name
        if '--bare' in args:
            dir += '.git'
        args.append(dir)

        self.gitm('clone', *args, redirect=False).returncode
        self.gitm('config', 'remote.origin.gitlab-id', repo.id, cwd=dir)
        if hasattr(repo, 'forked_from_project'):
            os.chdir(dir)
            self.set_origin(opts)
            self.gitm('fetch', 'upstream', redirect=False)

    @command
    @needs_repo
    def create(self, opts):
        """[--private|--internal] [-d <description>]
           Create a repository on gitlab to push to"""
        root = self.gitm('rev-parse', '--show-toplevel').stdout.strip()
        name = os.path.basename(root)
        if name in [x.name for x in self.gl.Project()]:
            err("Repository already exists")
        visibility_level = 20 # public
        if opts['--internal']:
            visibility_level = 10
        elif opts['--private']:
            visibility_level = 10
        glapi.Project(self.gl, {'name': name, 'description': opts['<description>'] or "", 'visibility_level': visibility_level}).save()
        opts['remotes'] = self.get_remotes(opts)
        self.set_origin(opts)

    @command
    def fork(self, opts):
        """[--ssh|--http] [<repo>]
           Fork a repo and clone it"""
        do_clone = bool(opts['<repo>'])
        repo = opts['remotes']['.dwim']
        if repo.owner.username == self.me.username:
            err("You cannot fork your own repos")

        if repo.name in [x.name for x in self.gl.Project()]:
            err("Repository already exists")

        opts['remotes']['.dwim'] = repo.fork()

        if do_clone:
            self.clone(opts)
        else:
            self.set_origin(opts)

    @command
    def issue(self, opts):
        """[<repo>] [--parent] [<issue>...]
           Show issue details or report an issue"""
        if opts['<repo>'] and opts['<repo>'].isdigit():
            # Let's assume it's an issue
            opts['<issue>'].insert(0, opts['<repo>'])
        repo = opts['remotes']['.dwim']
        # There's no way to fetch an issue by iid. Abuse search.
        issues = repo.Issue()
        for issue in opts['<issue>']:
            issue = int(issue)
            issue = [x for x in issues if x.iid == issue][0]
            print(wrap(issue.title, attr.bright, attr.underline))
            print(issue.description)
            print(self.issue_url(issue))
        if not opts['<issue>']:
            body = """
# Reporting an issue on %s/%s
# Please describe the issue as clarly as possible. Lines starting with '#' will
# be ignored, the first line will be used as title for the issue.
#""" % (repo.owner.username, repo.name)
            title, body = self.edit_msg(body, 'ISSUE_EDITMSG')
            if not body:
                err("Empty issue message")

            issue = glapi.ProjectIssue(self.gl, {'project_id': repo.id, 'title': title, 'description': body})
            issue.save()
            print("Issue %d created %s" % (issue.iid, self.issue_url(issue)))

    @command
    def issues(self, opts):
        """[<repo>] [--parent] [<filter>...]
           List issues in a repository"""
        repo = opts['remotes']['.dwim']
        if not repo:
            repos = list(self.gl.Project())
        else:
            repos = [repo]
        for repo in repos:
            if opts['--parent']:
                repo = self.parent_repo(repo) or repo
            filters = dict([x.split('=', 1) for x in opts['<filter>']])
            issues = repo.Issue(**filters)
            if not issues:
                continue
            print(wrap("Issues for %s/%s" % (repo.owner.username, repo.name), attr.bright))
            for issue in issues:
                print("[%d] %s %s" % (issue.iid, issue.title, self.issue_url(issue)))

    @command
    def log(self, opts):
        """[<repo>]
           Display GitHub log for a repository"""
        repo = opts['remotes']['.dwim']
        if not repo:
            return
        now = datetime.datetime.now()
        for event in reversed(repo.Event()):
            ts = datetime.datetime.strptime(event.created_at, '%Y-%m-%dT%H:%M:%S.%fZ')
            event.data = event.data or {}
            if ts.year == now.year:
                if (ts.month, ts.day) == (now.month, now.day):
                    ts = wrap(ts.strftime("%H:%M"), attr.faint)
                else:
                    ts = wrap(ts.strftime("%m/%d %H:%M"), attr.faint)
            else:
                ts = wrap(ts.strftime("%Y/%m/%d %H:%M"), attr.faint)
            if event.action_name == 'joined':
                print('%s %s joined' % (ts, event.author_username))
            elif event.target_type == 'Issue':
                issue = glapi.ProjectIssue(self.gl, event.target_id, project_id=event.project_id)
                print('%s %s %s issue %s (%s)' % (ts, event.author_username, event.action_name, issue.iid, issue.title))
            elif event.target_type == 'MergeRequest':
                issue = glapi.ProjectMergeRequest(self.gl, event.target_id, project_id=event.project_id)
                print('%s %s %s merge request %s (%s)' % (ts, event.author_username, event.action_name, issue.iid, issue.title))
            elif event.target_type == 'Note':
                print('%s %s created a comment' % (ts, event.author_username))
            elif 'total_commits_count' in event.data:
                if event.data['total_commits_count'] == 0:
                    print('%s %s deleted branch %s' % (ts, event.author_username, event.data['ref'][11:]))
                else:
                    print('%s %s pushed %s commits to %s' % (ts, event.author_username, event.data['total_commits_count'], event.data['ref'][11:]))
            elif 'ref' in event.data:
                print('%s %s created tag %s' % (ts, event.author_username, event.data['ref'][10:]))
            else:
                print(wrap("Cannot display event. Please file a bug at github.com/seveas/git-spindle\nincluding the following output:", attr.bright))
                pprint(event.json())

    @command
    @needs_repo
    def merge_request(self, opts):
        """[<branch1:branch2>]
           Opens a merge request to merge your branch1 to upstream branch2"""
        repo = opts['remotes']['.dwim']
        parent = self.parent_repo(repo) or repo
        # Which branch?
        src = opts['<branch1:branch2>'] or ''
        dst = None
        if ':' in src:
            src, dst = src.split(':', 1)
        if not src:
            src = self.gitm('rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()
        if not dst:
            dst = parent.default_branch

        if src == dst and parent == repo:
            err("Cannot file a merge request on the same branch")

        # Try to get the local commit
        commit = self.gitm('show-ref', 'refs/heads/%s' % src).stdout.split()[0]
        # Do they exist on github?
        srcb = repo.Branch(src)
        if not srcb:
            if raw_input("Branch %s does not exist in your gitlab repo, shall I push? [Y/n] " % src).lower() in ['y', 'Y', '']:
                self.gitm('push', repo.remote, src, redirect=False)
            else:
                err("Aborting")
        elif srcb and srcb.commit.id != commit:
            # Have we diverged? Then there are commits that are reachable from the github branch but not local
            diverged = self.gitm('rev-list', srcb.commit.id, '^' + commit)
            if diverged.stderr or diverged.stdout:
                if raw_input("Branch %s has diverged from gitlab, shall I push and overwrite? [y/N] " % src) in ['y', 'Y']:
                    self.gitm('push', '--force', repo.remote, src, redirect=False)
                else:
                    err("Aborting")
            else:
                if raw_input("Branch %s not up to date on gitlab, but can be fast forwarded, shall I push? [Y/n] " % src) in ['y', 'Y', '']:
                    self.gitm('push', repo.remote, src, redirect=False)
                else:
                    err("Aborting")

        dstb = parent.Branch(dst)
        if not dstb:
            err("Branch %s does not exist in %s/%s" % (dst, parent.owner.username, parent.name))

        # Do we have the dst locally?
        for remote in self.gitm('remote').stdout.strip().split("\n"):
            url = self.gitm('config', 'remote.%s.url' % remote).stdout.strip()
            if url in [parent.ssh_url_to_repo, parent.http_url_to_repo]:
                if not parent.public and url != parent.ssh_url_to_repo:
                    err("You should configure %s/%s to fetch via ssh, it is a private repo" % (parent.owner.username, parent.name))
                self.gitm('fetch', remote, redirect=False)
                break
        else:
            err("You don't have %s/%s configured as a remote repository" % (parent.owner.username, parent.name))

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
# Requesting a merge from %s/%s into %s/%s
#
# Please enter a message to accompany your merge request. Lines starting
# with '#' will be ignored, and an empty message aborts the request.
#""" % (repo.owner.username, src, parent.owner.username, dst)
        body += "\n# " + try_decode(self.gitm('shortlog', '%s/%s..%s' % (remote, dst, src)).stdout).strip().replace('\n', '\n# ')
        body += "\n#\n# " + try_decode(self.gitm('diff', '--stat', '%s^..%s' % (commits[0], commits[-1])).stdout).strip().replace('\n', '\n#')
        title, body = self.edit_msg("%s\n\n%s" % (title,body), 'merge_REQUEST_EDIT_MSG')
        if not body:
            err("No merge request message specified")

        merge = glapi.ProjectMergeRequest(self.gl, {'project_id': repo.id, 'target_project_id': parent.id, 'source_branch': src, 'target_branch': dst, 'title': title, 'description': body})
        merge.save()
        print("merge request %d created %s" % (merge.iid, self.merge_url(merge)))

    @command
    def mirror(self, opts):
        """[--ssh|--http] [--goblet] [<repo>]
           Mirror a repository, or all your repositories"""
        if opts['<repo>'] and opts['<repo>'] == '*':
            opts['<repo>'] = None
            for repo in self.gl.Project():
                opts['remotes']['.dwim'] = repo
                self.mirror(opts)
            return
        repo = opts['remotes']['.dwim']
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
            self.gitm('--git-dir', git_dir, 'fetch', '-q', 'origin', redirect=False)
            self.gitm('--git-dir', git_dir, 'remote', 'prune', 'origin', redirect=False)

        with open(os.path.join(git_dir, 'description'), 'w') as fd:
            if PY3:
                fd.write(repo.description or "")
            else:
                fd.write((repo.description or "").encode('utf-8'))
        if opts['--goblet']:
            self.gitm('--git-dir', git_dir, 'config', 'goblet.owner', repo.owner.name.encode('utf-8') or repo.owner.login)
            self.gitm('--git-dir', git_dir, 'config', 'goblet.cloneurlhttp', repo.http_url_to_repo)
            goblet_dir = os.path.join(git_dir, 'goblet')
            if not os.path.exists(goblet_dir):
                os.mkdir(goblet_dir, 0o777)
                os.chmod(goblet_dir, 0o777)


    @command
    def public_keys(self, opts):
        """[<user>]
           Lists all keys for a user"""
        if opts['<user>']:
            user = self.find_user(opts['<user>'][0])
        else:
            user = self.me
        if not user:
            err("No such user")
        try:
            for key in user.Key():
                print("%s %s" % (key.key, key.title or ''))
        except glapi.GitlabListError:
            # Permission denied, ignore
            pass

    @command
    def repos(self, opts):
        """[--no-forks]
           List all your repos"""
        repos = self.gl.Project()
        maxlen = max([len(x.name) for x in repos])
        for repo in repos:
            color = [attr.normal]
            if repo.visibility_level == 0:
                color.append(fgcolor.red)
            elif repo.visibility_level == 10:
                color.append(fgcolor.magenta)
            if hasattr(repo, 'forked_from_project'):
                if opts['--no-forks']:
                    continue
                color.append(attr.faint)
            name = repo.name
            if self.me.username != repo.owner.username:
                name = '%s/%s' % (repo.owner.username, name)
            msg = wrap(name, *color)
            if not PY3:
                msg = msg.encode('utf-8')
            print(msg)

    @command
    @needs_repo
    def set_origin(self, opts):
        """[--ssh|--http]
           Set the remote 'origin' to gitlab.
           If this is a fork, set the remote 'upstream' to the parent"""
        repo = opts['remotes']['.dwim']
        # Is this mine? No? Do I have a clone?
        if repo.owner.username != self.me.username:
            my_repo = self.find_repo(self.me.username, repo.name)
            if my_repo:
                repo = my_repo

        url = self.clone_url(repo, opts)
        if self.git('config', 'remote.origin.url').stdout.strip() != url:
            print("Pointing origin to %s" % url)
            self.gitm('config', 'remote.origin.url', url)
            self.gitm('config', 'remote.origin.gitlab-id', repo.id)
            self.gitm('fetch', 'origin', redirect=False)

        parent = self.parent_repo(repo)
        if parent:
            url = self.clone_url(parent, opts)
            if self.git('config', 'remote.upstream.url').stdout.strip() != url:
                print("Pointing upstream to %s" % url)
                self.gitm('config', 'remote.upstream.url', url)
                self.gitm('config', 'remote.upstream.gitlab-id', parent.id)
            self.gitm('config', 'remote.upstream.fetch', '+refs/heads/*:refs/remotes/upstream/*')

        for branch in self.git('for-each-ref', 'refs/heads/**').stdout.strip().splitlines():
            branch = branch.split(None, 2)[-1][11:]
            if self.git('for-each-ref', 'refs/remotes/origin/%s' % branch).stdout.strip():
                if self.gitm('config', 'branch.%s.remote' % branch).returncode != 0:
                    print("Marking %s as remote-tracking branch" % branch)
                    self.gitm('config', 'branch.%s.remote' % branch, 'origin')
                    self.gitm('config', 'branch.%s.merge' % branch, 'refs/heads/%s' % branch)

    @command
    def whoami(self, opts):
        """\nDisplay GitLab user info"""
        opts['<user>'] = [self.me]
        self.whois(opts)

    @command
    def whois(self, opts):
        """<user>...
           Display GitLab user info"""
        for user in opts['<user>']:
            if not isinstance(user, (glapi.User, glapi.CurrentUser)):
                user_ = self.find_user(user)
                if not user_:
                    print("No such user: %s" % user)
                    continue
                user = user_
            print(wrap("%s (id %d)" % (user.name or user.username, user.id), attr.bright, attr.underline))
            print('Profile   %s' % self.profile_url(user))
            if hasattr(user, 'email'):
                if user.email:
                    print('Email     %s' % user.email)
                if user.website_url:
                    print('Website   %s' % user.website_url)
                if user.twitter:
                    print('Twitter   %s' % user.twitter)
                if user.linkedin:
                    print('LinkedIn  %s' % user.linkedin)
                if user.bio:
                    if '\n' in user.bio:
                        bio = user.bio[:user.bio.index('\n')] + '...'
                    else:
                        bio = user.bio
                    print('Bio       %s' % user.bio)
            try:
                for pkey in user.Key():
                    algo, key = pkey.key.split()
                    algo = algo[4:].upper()
                    if pkey.title:
                        print("%s key%s...%s (%s)" % (algo, ' ' * (6 - len(algo)), key[-10:], pkey.title))
                    else:
                        print("%s key%s...%s" % (algo, ' ' * (6 - len(algo)), key[-10:]))

            except glapi.GitlabListError:
                # Permission denied, ignore
                pass

    # And debugging

    @hidden_command
    def run_shell(self, opts):
        """\nDebug method to run a shell"""
        import code
        import readline
        import rlcompleter
        opts['remotes'] = self.get_remotes(opts)

        data = {
            'self':    self,
            'gitlab':  glapi,
            'opts':    opts,
        }
        readline.set_completer(rlcompleter.Completer(data).complete)
        readline.parse_and_bind("tab: complete")
        shl = code.InteractiveConsole(data)
        shl.interact()
        sys.exit(1)
