from gitspindle import *
from gitspindle.ansi import *
import gitspindle.glapi as glapi
import base64
import datetime
import getpass
import glob
import json
import os
import requests
import sys
import time
import webbrowser

class GitLab(GitSpindle):
    prog = 'git lab'
    what = 'GitLab'
    spindle = 'gitlab'
    hosts = ['gitlab.com', 'www.gitlab.com']
    api = glapi
    access_levels = {
        'guest':     10,
        'reporter':  20,
        'developer': 30,
        'master':    40,
        'owner':     50,
    }
    access_levels_r = dict([(value, key) for (key, value) in access_levels.items()])

    # Support functions
    def login(self):
        self.gl = None
        host = self.config('host') or 'https://gitlab.com'
        if not host.startswith(('http://', 'https://')):
            try:
                requests.get('https://' + host)
            except:
                err("%s is not reachable via https. Use http://%s to use the insecure http protocol" % (host, host))
            host = 'https://' + host
        self.host = host

        user = self.config('user')
        if not user:
            user = raw_input("GitLab user: ").strip()
            self.config('user', user)

        token = self.config('token')
        if not token:
            password = getpass.getpass("GitLab password: ")
            self.gl = glapi.Gitlab(host, email=user, password=password)
            self.gl.auth()
            token = self.gl.user.private_token
            self.config('token', token)
            location = '%s - do not share this file' % self.config_file
            if self.use_credential_helper:
                location = 'git\'s credential helper'
            print("Your GitLab authentication token is now stored in %s" % location)

        if not user or not token:
            err("No user or token specified")

        if not self.gl:
            self.gl = glapi.Gitlab(host, email=user, private_token=token)
            try:
                self.gl.auth()
            except glapi.GitlabAuthenticationError:
                # Token obsolete
                self.config('token', None)
                self.login()
        self.me = self.gl.user
        self.my_login = self.me.username

    def parse_url(self, url):
        return ([self.my_login] + url.path.split('/'))[-2:]

    def get_repo(self, remote, user, repo):
        if remote:
            id = self.git('config', 'remote.%s.gitlab-id' % remote).stdout.strip()
            if id and id.isdigit():
                return self.gl.Project(id)

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
            return repo.http_url_to_repo
        if repo.namespace.path == self.my_login:
            return repo.ssh_url_to_repo
        return repo.http_url_to_repo

    def parent_repo(self, repo):
       if getattr(repo, 'forked_from_project', False):
           return self.gl.Project(repo.forked_from_project['id'])

    def find_repo(self, user, name):
        try:
            project = self.gl.Project('%s%%2F%s' % (user, name))
            # Yes, we need to check the name. Requesting foo.broken returns the foo project.
            if project.path != name:
                return None
            return project
        except glapi.GitlabGetError:
            pass

    # There's no way to fetch a user by username. Abuse search.
    def find_user(self, username):
        try:
            for user in self.gl.User(search=username):
                if user.username == username:
                    return user
        except glapi.GitlabListError:
            pass

    # There's no way to fetch a group by name. Abuse search.
    def find_group(self, name):
        try:
            for group in self.gl.Group(search=name):
                if group.path == name:
                    return group
        except glapi.GitlabListError:
            pass

    def profile_url(self, user):
        return '%s/u/%s' % (self.host, user.username)

    def merge_url(self, merge):
        repo = self.gl.Project(merge.project_id)
        return '%s/merge_requests/%d' % (repo.web_url, merge.iid)

    def api_root(self):
        if hasattr(self, 'gl') and self.gl:
            return self.gl._url
        host = self.config('host')
        if not host:
            return 'https://gitlab.com/api/v3'
        host = host.rstrip('/') + '/api/v3'
        if not host.startswith(('http://', 'https://')):
            host = 'https://' + host
        return host

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
    def add_member(self, opts):
        """[--access-level=guest|reporter|developer|master|owner] <user>...
           Add a project member"""
        repo = self.repository(opts)
        for user in opts['<user>']:
            user_ = self.find_user(user)
            if not user_:
                print("No such user: %s" % user)
                continue
            user = user_
            access_level = self.access_levels[opts['--access-level'] or 'developer']
            glapi.ProjectMember(self.gl, {'project_id': repo.id, 'user_id': user.id, 'access_level': access_level}).save()

    @command
    def add_remote(self, opts):
        """[--ssh|--http] <user> [<name>]
           Add user's fork as a named remote. The name defaults to the user's loginname"""
        dwim = self.repository(opts)
        user = opts['<user>'][0]
        name = opts['<name>'] or user
        repo = self.find_repo(user, dwim.path)
        if not repo:
            err("Repository %s/%s does not exist" % (user, dwim.path))
        url = self.clone_url(repo, opts)
        self.gitm('remote', 'add', name, url)
        self.gitm('config', 'remote.%s.gitlab-id' % name, repo.id)
        self.gitm('fetch', name, redirect=False)

    @command
    def apply_merge(self, opts):
        """[--ssh|--http] <merge-request-number>
           Applies a merge request as a series of cherry-picks"""
        repo = self.repository(opts)
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
            if not self.question("Continue?", default=False):
                sys.exit(1)
        # Fetch mr if needed
        sha = self.git('rev-parse', '--verify', 'refs/merge/%d/head' % mr.iid).stdout.strip()
        if not sha:
            print("Fetching merge request")
            url = self.clone_url(glapi.Project(self.gl, mr.source_project_id), opts)
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
        repo = self.repository(opts)
        section_map = {'wiki': 'wikis/home', 'files': 'tree/%s' % repo.default_branch,
                       'commits': 'commits/%s' % repo.default_branch, 'settings': 'edit',
                       'graphs': 'graphs/%s' % repo.default_branch}
        url = repo.web_url
        if opts['<section>']:
            url += '/' + section_map.get(opts['<section>'], opts['<section>'])
        webbrowser.open_new(url)

    @command
    def calendar(self, opts):
        """[<user>]
           Show a timeline of a user's activity"""
        user = (opts['<user>'] or [self.my_login])[0]
        user = self.find_user(user)
        months = []
        rows = [[],[],[],[],[],[],[]]
        commits = []
        data = user.calendar()

        first = datetime.datetime.today() - datetime.timedelta(365)
        wd = (first.weekday()+1) % 7
        for i in range(wd):
            rows[i].append((None,None))
        if wd:
            months.append(first.month)
        for back in range(364, -1, -1):
            date = datetime.datetime.today() - datetime.timedelta(back)
            ts = date.strftime('%Y-%m-%d')
            wd = (date.weekday()+1) % 7
            count = data.get(ts, 0)
            rows[wd].append((date.day, count))
            if not wd:
                months.append(date.month)
            if count:
                commits.append(count)

        # Print months
        sys.stdout.write("  ")
        last = -1
        skip = months[2] != months[0]
        monthtext = ('', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
        for month in months:
            if month != last:
                sys.stdout.write(monthtext[month] + ' ')
                skip = True
                last = month
            elif not skip:
                sys.stdout.write('  ')
            else:
                skip = False
        print("")

        # Print commits
        days = 'SMTWTFS'
        commits.sort()
        print(commits)
        if len(commits) < 2:
            p5 = p15 = p35 = 0
        else:
            p5  = commits[min(int(round(len(commits) * 0.95)), len(commits)-1)]
            p15 = commits[min(int(round(len(commits) * 0.85)), len(commits)-1)]
            p35 = commits[min(int(round(len(commits) * 0.65)), len(commits)-1)]
        blob1 = b'\xe2\x96\xa0'.decode('utf-8')
        blob2 = b'\xe2\x97\xbc'.decode('utf-8')
        for rnum, row in enumerate(rows):
            if rnum % 2:
                sys.stdout.write(days[rnum] + " ")
            else:
                sys.stdout.write("  ")
            for (day, count) in row:
                if count is None:
                    color = attr.conceal
                elif count > p5:
                    color = fgcolor.xterm(22)
                elif count > p15:
                    color = fgcolor.xterm(28)
                elif count > p35:
                    color = fgcolor.xterm(64)
                elif count:
                    color = fgcolor.xterm(65)
                else:
                    color = fgcolor.xterm(237)
                if day == 1:
                    msg = wrap(blob2, attr.underline, color)
                    if not PY3:
                        msg = msg.encode('utf-8')
                    sys.stdout.write(msg)
                else:
                    msg = wrap(blob1, color)
                    if not PY3:
                        msg = msg.encode('utf-8')
                    sys.stdout.write(msg)
                sys.stdout.write(' ')
            print("")


    @command
    def cat(self, opts):
        """<file>...
           Display the contents of a file on GitLab"""
        for file in opts['<file>']:
            repo, ref, file = ([None, None] + file.split(':',2))[-3:]
            user = None
            if repo:
                user, repo = ([None] + repo.split('/'))[-2:]
                repo = self.find_repo(user or self.my_login, repo)
            else:
                repo = self.repository(opts)
                file = self.rel2root(file).lstrip('/')

            try:
                file = repo.File(ref=ref or repo.default_branch, file_path=file)
                os.write(sys.stdout.fileno(), base64.b64decode(file.content))
            except glapi.GitlabGetError:
                sys.stderr.write("No such file: %s\n" % file)

    @command
    def clone(self, opts, repo=None):
        """[--ssh|--http] [--triangular [--upstream-branch=<branch>]] [--parent] [git-clone-options] <repo> [<dir>]
           Clone a repository by name"""
        if not repo:
            repo = self.repository(opts)
        url = self.clone_url(repo, opts)

        args = opts['extra-opts']
        args.append(url)
        dir = opts['<dir>'] and opts['<dir>'][0] or repo.path
        if '--bare' in args:
            dir += '.git'
        args.append(dir)

        self.gitm('clone', *args, redirect=False).returncode
        self.gitm('config', 'remote.origin.gitlab-id', repo.id, cwd=dir)
        if hasattr(repo, 'forked_from_project'):
            os.chdir(dir)
            self.set_origin(opts, repo=repo)

    @command
    def create(self, opts):
        """[--private|--internal] [--group=<group>] [--description=<description>]
           Create a repository on gitlab to push to"""
        root = self.gitm('rev-parse', '--show-toplevel').stdout.strip()
        name = os.path.basename(root)
        if (opts['--group'] or self.my_login, name) in [(x.namespace.path, x.path) for x in self.gl.Project()]:
            err("Repository already exists")
        visibility_level = 20 # public
        if opts['--internal']:
            visibility_level = 10
        elif opts['--private']:
            visibility_level = 0
        kwargs = {'name': name, 'description': opts['--description'] or "", 'visibility_level': visibility_level}
        if opts['--group']:
            group = self.find_group(opts['--group'])
            if not group:
                err("Group %s could not be found" % opts['--group'])
            kwargs['namespace_id'] = group.id
        repo = glapi.Project(self.gl, kwargs)
        i = 0
        success = False
        while not success:
            try:
                repo.save()
                success = True
            except glapi.GitlabCreateError as gce:
                i += 1
                time.sleep(1)
                if (gce.response_code != 400) \
                        or (not isinstance(gce.error_message, dict)) \
                        or (not 'base' in gce.error_message) \
                        or (not isinstance(gce.error_message['base'], list)) \
                        or (not 'The project is still being deleted. Please try again later.' in gce.error_message['base']) \
                        or (i >= 120):
                    raise
        if 'origin' in self.remotes():
            print("Remote 'origin' already exists, adding the GitLab repository as 'gitlab'")
            self.set_origin(opts, repo=repo, remote='gitlab')
        else:
            self.set_origin(opts, repo=repo)

    @command
    def fetch(self, opts):
        """[--ssh|--http] <user> [<refspec>]
           Fetch refs from a user's fork"""
        repo = self.repository(opts)
        user = opts['<user>'][0]
        refspec = opts['<refspec>'] or 'refs/heads/*'
        repo = self.find_repo(user, repo.path)
        if not repo:
            err("Repository %s/%s does not exist" % (user, repo.path))
        if ':' not in refspec:
            if not refspec.startswith('refs/'):
                refspec += ':' + 'refs/remotes/%s/' % repo.namespace.path + refspec
            else:
                refspec += ':' + refspec.replace('refs/heads/', 'refs/remotes/%s/' % repo.namespace.path)
        url = self.clone_url(repo, opts)
        self.gitm('fetch', url, refspec, redirect=False)

    @command
    def fork(self, opts):
        """[--ssh|--http] [--triangular [--upstream-branch=<branch>]] [<repo>]
           Fork a repo and clone it"""
        do_clone = bool(opts['<repo>'])
        repo = self.repository(opts)
        if repo.namespace.path == self.my_login:
            err("You cannot fork your own repos")

        my_repo = self.find_repo(self.my_login, repo.path)
        if my_repo:
            err("Repository already exists")

        i = 0
        success = False
        while not success:
            try:
                my_fork = repo.fork()
                success = True
            except glapi.GitlabForkError as gfe:
                i += 1
                time.sleep(1)
                if (gfe.response_code != 409) \
                        or (not isinstance(gfe.error_message, dict)) \
                        or (not 'base' in gfe.error_message) \
                        or (not isinstance(gfe.error_message['base'], list)) \
                        or (not 'The project is still being deleted. Please try again later.' in gfe.error_message['base']) \
                        or (i >= 120):
                    raise

        self.wait_for_repo(my_fork.owner.username, my_fork.name, opts)

        if do_clone:
            self.clone(opts, repo=my_fork)
        else:
            self.set_origin(opts, repo=my_fork)

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
            issues = repo.Issue(iid=issue_no)
            if len(issues):
                issue = issues[0]
                print(wrap(issue.title.encode(sys.stdout.encoding, errors='backslashreplace').decode(sys.stdout.encoding), attr.bright, attr.underline))
                print(issue.description.encode(sys.stdout.encoding, errors='backslashreplace').decode(sys.stdout.encoding))
                print(issue.web_url)
            else:
                print('No issue with id %s found in repository %s' % (issue_no, repo.path_with_namespace))
        if not opts['<issue>']:
            extra = """Reporting an issue on %s/%s
Please describe the issue as clearly as possible. Lines starting with '#' will
be ignored, the first line will be used as title for the issue.""" % (repo.namespace.path, repo.path)
            title, body = self.edit_msg(None, '', extra, 'ISSUE_EDITMSG')
            if not body:
                err("Empty issue message")

            try:
                issue = glapi.ProjectIssue(self.gl, {'project_id': repo.id, 'title': title, 'description': body})
                issue.save()
                print("Issue %d created %s" % (issue.iid, issue.web_url))
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
            repos = list(self.gl.Project())
        else:
            repos = [self.repository(opts)]
        for repo in repos:
            if opts['--parent']:
                repo = self.parent_repo(repo) or repo
            filters = dict([x.split('=', 1) for x in opts['<filter>']])
            issues = repo.Issue(**filters)
            mergerequests = repo.MergeRequest(state='opened')
            if not issues and not mergerequests:
                continue
            if issues:
                print(wrap("Issues for %s/%s" % (repo.namespace.path, repo.path), attr.bright))
                for issue in issues:
                    print("[%d] %s %s" % (issue.iid, issue.title.encode(sys.stdout.encoding, errors='backslashreplace').decode(sys.stdout.encoding), issue.web_url))
            if mergerequests:
                print(wrap("Merge requests for %s/%s" % (repo.namespace.path, repo.path), attr.bright))
                for mr in mergerequests:
                    print("[%d] %s %s" % (mr.iid, mr.title.encode(sys.stdout.encoding, errors='backslashreplace').decode(sys.stdout.encoding), self.merge_url(mr)))

    @command
    def log(self, opts):
        """[<repo>]
           Display GitLab log for a repository"""
        repo = self.repository(opts)
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
    def ls(self, opts):
        """[<dir>...]
           Display the contents of a directory on GitLab"""
        for arg in opts['<dir>'] or ['']:
            repo, ref, file = ([None, None] + arg.split(':',2))[-3:]
            user = None
            if repo:
                user, repo = ([None] + repo.split('/'))[-2:]
                repo = self.find_repo(user or self.my_login, repo)
            else:
                repo = self.repository(opts)
                file = self.rel2root(file).lstrip('/')

            try:
                content = repo.tree(ref_name=ref or repo.default_branch, path=file)
            except glapi.GitlabGetError:
                err("No such file: %s" % arg)
            if not content:
                err("Not a directory: %s" % arg)
            mt = max([len(file['type']) for file in content])
            fmt = "%%(mode)s %%(type)-%ds %%(id).7s %%(name)s" % (mt, )
            for file in content:
                print(fmt % file)

    @command
    def members(self, opts):
        """[<repo>]
           List repo memberships"""
        repo = self.repository(opts)
        members = repo.Member()
        members.sort(key=lambda member: (-member.access_level, member.username))
        maxlen = members and max([len(member.username) for member in members]) or 0
        fmt = "%%s %%-%ds (%%s)" % maxlen
        for member in members:
            print(fmt % (wrap("%-9s" % self.access_levels_r[member.access_level], attr.faint), member.username, member.name))

    @command
    def merge_request(self, opts):
        """[--yes] [<yours:theirs>]
           Opens a merge request to merge your branch to an upstream branch"""
        repo = self.repository(opts)
        parent = self.parent_repo(repo) or repo
        # Which branch?
        src = opts['<yours:theirs>'] or ''
        dst = None
        if ':' in src:
            src, dst = src.split(':', 1)
        if not src:
            src = self.gitm('rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()
        if not dst:
            dst = parent.default_branch
            if tracking_branch.startswith('refs/remotes/'):
                tracking_remote, tracking_branch = tracking_branch.split('/', 3)[-2:]
                if tracking_branch != src or repo.remote != tracking_remote:
                    # Interesting. We're not just tracking a branch in our clone!
                    dst = tracking_branch

        if src == dst and parent == repo:
            err("Cannot file a merge request on the same branch")

        # Try to get the local commit
        commit = self.gitm('show-ref', 'refs/heads/%s' % src).stdout.split()[0]
        # Do they exist on GitLab?
        try:
            srcb = repo.Branch(src)
        except glapi.GitlabGetError:
            srcb = None
            if self.question("Branch %s does not exist in your GitLab repo, shall I push?" % src):
                self.gitm('push', '-u', repo.remote, src, redirect=False)
            else:
                err("Aborting")
        if srcb and srcb.commit.id != commit:
            # Have we diverged? Then there are commits that are reachable from the GitLab branch but not local
            diverged = self.gitm('rev-list', srcb.commit.id, '^' + commit)
            if diverged.stderr or diverged.stdout:
                if self.question("Branch %s has diverged from GitLab, shall I push and overwrite?" % src, default=False):
                    self.gitm('push', '--force', repo.remote, src, redirect=False)
                else:
                    err("Aborting")
            else:
                if self.question("Branch %s not up to date on GitLab, but can be fast forwarded, shall I push?" % src):
                    self.gitm('push', repo.remote, src, redirect=False)
                else:
                    err("Aborting")

        dstb = parent.Branch(dst)
        if not dstb:
            err("Branch %s does not exist in %s/%s" % (dst, parent.namespace.path, parent.path))

        # Do we have the dst locally?
        for remote in self.gitm('remote').stdout.strip().split("\n"):
            url = self.gitm('config', 'remote.%s.url' % remote).stdout.strip()
            if url in [parent.ssh_url_to_repo, parent.http_url_to_repo]:
                if not parent.public and url != parent.ssh_url_to_repo:
                    err("You should configure %s/%s to fetch via ssh, it is a private repo" % (parent.namespace.path, parent.path))
                self.gitm('fetch', remote, redirect=False)
                break
        else:
            err("You don't have %s/%s configured as a remote repository" % (parent.namespace.path, parent.path))

        # How many commits?
        accept_empty_body = False
        commits = try_decode(self.gitm('log', '--pretty=%H', '%s/%s..%s' % (remote, dst, src)).stdout).strip().split()
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

        extra = """Requesting a merge from %s/%s into %s/%s

Please enter a message to accompany your merge request. Lines starting
with '#' will be ignored, and an empty message aborts the request.""" % (repo.namespace.path, src, parent.namespace.path, dst)
        body += "\n\n" + try_decode(self.gitm('shortlog', '%s/%s..%s' % (remote, dst, src)).stdout).strip()
        body += "\n\n" + try_decode(self.gitm('diff', '--stat', '%s^..%s' % (commits[0], commits[-1])).stdout).strip()
        title, body = self.edit_msg(title, body, extra, 'MERGE_REQUEST_EDIT_MSG')
        if not body and not accept_empty_body:
            err("No merge request message specified")

        try:
            merge = glapi.ProjectMergeRequest(self.gl, {'project_id': repo.id, 'target_project_id': parent.id, 'source_branch': src, 'target_branch': dst, 'title': title, 'description': body})
            merge.save()
            print("merge request %d created %s" % (merge.iid, self.merge_url(merge)))
        except:
            filename = self.backup_message(title, body, 'merge-request-message-')
            err("Failed to create a merge request, the merge request text has been saved in %s" % filename)

    @command
    def mirror(self, opts):
        """[--ssh|--http] [--goblet] [<repo>]
           Mirror a repository, or all your repositories"""
        if opts['<repo>'] and opts['<repo>'] == '*':
            for repo in self.gl.Project():
                opts['<repo>'] = '%s/%s' % (repo.namespace.path, name)
                self.mirror(opts)
            return
        repo = self.repository(opts)
        git_dir = repo.path + '.git'
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
            self.gitm('--git-dir', git_dir, 'config', 'goblet.owner', repo.owner.name.encode('utf-8') or repo.owner.login)
            self.gitm('--git-dir', git_dir, 'config', 'goblet.cloneurlhttp', repo.http_url_to_repo)
            goblet_dir = os.path.join(git_dir, 'goblet')
            if not os.path.exists(goblet_dir):
                os.mkdir(goblet_dir, 0o777)
                os.chmod(goblet_dir, 0o777)

    @command
    def protect(self, opts):
        """<branch>
           Protect a branch against force-pushes"""
        repo = self.repository(opts)
        for branch in repo.Branch():
            if branch.name == opts['<branch>']:
                branch.protect()
                break

    @command
    def protected(self, opts):
        """\nList protected branches"""
        repo = self.repository(opts)
        for branch in repo.Branch():
            if branch.protected:
                print(branch.name)

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
    def remove_member(self, opts):
        """<user>...
           Remove a user's membership"""
        repo = self.repository(opts)
        for member in repo.Member():
            if member.username in opts['<user>']:
                member.delete()

    @command
    def repos(self, opts):
        """[--no-forks]
           List all your repos"""
        repos = self.gl.Project()
        if not repos:
            return
        maxlen = max([len(x.name) for x in repos])
        fmt = u"%%-%ds %%s" % maxlen
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
            name = repo.path
            if self.my_login != repo.namespace.path:
                name = '%s/%s' % (repo.namespace.path, name)
            desc = ' '.join((repo.description or '').splitlines())
            msg = wrap(fmt % (name, desc), *color)
            if not PY3:
                msg = msg.encode('utf-8')
            print(msg)

    @command
    def set_origin(self, opts, repo=None, remote='origin'):
        """[--ssh|--http] [--triangular [--upstream-branch=<branch>]]
           Set the remote 'origin' to gitlab.
           If this is a fork, set the remote 'upstream' to the parent"""
        if not repo:
            repo = self.repository(opts)
            # Is this mine? No? Do I have a clone?
            if repo.namespace.path != self.my_login:
                my_repo = self.find_repo(self.my_login, repo.path)
                if my_repo:
                    repo = my_repo

        url = self.clone_url(repo, opts)
        if self.git('config', 'remote.%s.url' % remote).stdout.strip() != url:
            print("Pointing %s to %s" % (remote, url))
            self.gitm('config', 'remote.%s.url' % remote, url)
            self.gitm('config', 'remote.%s.gitlab-id' % remote, repo.id)
        self.gitm('config', '--replace-all', 'remote.%s.fetch' % remote, '+refs/heads/*:refs/remotes/%s/*' % remote)

        parent = self.parent_repo(repo)
        if parent:
            url = self.clone_url(parent, opts)
            if self.git('config', 'remote.upstream.url').stdout.strip() != url:
                print("Pointing upstream to %s" % url)
                self.gitm('config', 'remote.upstream.url', url)
                self.gitm('config', 'remote.upstream.gitlab-id', parent.id)
            self.gitm('config', 'remote.upstream.fetch', '+refs/heads/*:refs/remotes/upstream/*')

        if self.git('ls-remote', remote).stdout.strip():
            self.gitm('fetch', remote, redirect=False)
        if parent:
            self.gitm('fetch', 'upstream', redirect=False)

        if remote != 'origin':
            return

        self.set_tracking_branches(remote, upstream="upstream", triangular=opts['--triangular'], upstream_branch=opts['--upstream-branch'])

    @command
    def unprotect(self, opts):
        """<branch>
           Remove force-push protection from a branch"""
        repo = self.repository(opts)
        for branch in repo.Branch():
            if branch.name == opts['<branch>']:
                branch.unprotect()
                break

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
                    algo, key = pkey.key.split()[:2]
                    algo = algo[4:].upper()
                    if pkey.title:
                        print("%s key%s...%s (%s)" % (algo, ' ' * (6 - len(algo)), key[-10:], pkey.title))
                    else:
                        print("%s key%s...%s" % (algo, ' ' * (6 - len(algo)), key[-10:]))

            except glapi.GitlabListError:
                # Permission denied, ignore
                pass
