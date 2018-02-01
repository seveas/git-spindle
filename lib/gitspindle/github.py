from gitspindle import *
from gitspindle.ansi import *
import datetime
import getpass
import github3
import github3.gists
import glob
import os
import re
import requests
import socket
import sys
import tempfile
import time
import webbrowser

class GitHub(GitSpindle):
    prog = 'git hub'
    what = 'GitHub'
    spindle = 'github'
    hosts = ['github.com', 'www.github.com', 'gist.github.com']
    api = github3

    # Support functions
    def login(self):
        host = self.config('host')
        if host and host not in ('https://api.github.com', 'api.github.com'):
            if not host.startswith(('http://', 'https://')):
                try:
                    requests.get('https://' + host)
                except:
                    err("%s is not reachable via https. Use http://%s to use the insecure http protocol" % (host, host))
                host = 'https://' + host
            self.gh = github3.GitHubEnterprise(url=host)
        else:
            self.gh = github3.GitHub()

        user = self.config('user')
        if not user:
            user = raw_input("GitHub user: ").strip()
            self.config('user', user)

        token = self.config('token')
        if not token:
            password = getpass.getpass("GitHub password: ")
            self.gh.login(user, password, two_factor_callback=lambda: prompt_for_2fa(user))
            scopes = ['user', 'repo', 'gist', 'admin:public_key', 'admin:repo_hook', 'admin:org']
            if user.startswith('git-spindle-test-'):
                scopes.append('delete_repo')
            name = "GitSpindle on %s" % socket.gethostname()
            try:
                auth = self.gh.authorize(user, password, scopes, name, "http://seveas.github.com/git-spindle")
            except github3.GitHubError:
                type, exc = sys.exc_info()[:2]
                if not hasattr(exc, 'response'):
                    raise
                response = exc.response
                if response.status_code != 422:
                    raise
                for error in response.json()['errors']:
                    if error['resource'] == 'OauthAccess' and error['code'] == 'already_exists':
                        if os.getenv('DEBUG') or self.question('An OAuth token for this host already exists. Shall I delete it?', default=False):
                            for auth in self.gh.iter_authorizations():
                                if auth.app['name'] in (name, '%s (API)' % name):
                                    auth.delete()
                            auth = self.gh.authorize(user, password, scopes, name, "http://seveas.github.com/git-spindle")
                        else:
                            err('Unable to create an OAuth token')
                        break
                else:
                    raise
            if auth is None:
                err("Authentication failed")
            token = auth.token
            self.config('token', token)
            self.config('auth-id', auth.id)
            location = '%s - do not share this file' % self.config_file
            if self.use_credential_helper:
                location = 'git\'s credential helper'
            print("A GitHub authentication token is now stored in %s" % location)
            print("To revoke access, visit https://github.com/settings/applications")

        if not user or not token:
            err("No user or token specified")
        self.gh.login(username=user, token=token)
        try:
            self.me = self.gh.user()
            self.my_login = self.me.login
        except github3.GitHubError:
            # Token obsolete
            self.config('token', None)
            self.login()

    def parse_url(self, url):
        if url.hostname == 'gist.github.com':
            return ['gist', url.path.split('/')[-1]]
        else:
            return ([self.my_login] + url.path.split('/'))[-2:]

    def get_repo(self, remote, user, repo):
        if user == 'gist':
            # This is a gist, not a normal repo
            repo_ = self.gh.gist(repo)
            if not repo_:
                err("Gist %s does not exist" % repo)
        else:
            repo_ = self.gh.repository(user, repo)

        return repo_

    def parent_repo(self, repo):
        if repo.fork:
            # In search results or lists parent info is not returned with a repository
            return repo.parent or self.gh.repository(repo.owner.login, repo.name).parent

    def clone_url(self, repo, opts):
        if opts['--ssh'] or repo.private:
            return repo.ssh_url
        if opts['--http']:
            return repo.clone_url
        if opts['--git']:
            return repo.git_url
        if self.my_login == repo.owner.login:
            return repo.ssh_url
        return repo.clone_url

    def api_root(self):
        if hasattr(self, 'gh'):
            return self.gh._session.base_url
        host = self.config('host')
        if not host:
            return 'https://api.github.com'
        return host.rstrip('/') + '/api/v3'

    def find_template(self, repo, template):
        template = template.lower()
        contents = None
        for dir in ('/', '/.github/'):
            files = repo.contents(dir)
            if not files or not hasattr(files, 'items'):
                continue
            files = dict([(x[0].lower(), x[1]) for x in files.items()])

            if template in files:
                contents = files[template]
            else:
                for file in files:
                    if file.startswith(template + '.'):
                        contents = files[file]
        if contents:
            contents = contents.name, self.gh._session.get(contents._json_data['download_url'], stream=True).text
        return contents

    # Commands

    @command
    def add_collaborator(self, opts):
        """<user>...
           Add a user as collaborator"""
        repo = self.repository(opts)
        for user in opts['<user>']:
            repo.add_collaborator(user)

    @command
    def add_deploy_key(self, opts):
        """[--read-only] <key>...
           Add a deploy key"""
        repo = self.repository(opts)
        url = repo._build_url('keys', base_url=repo._api)
        for arg in opts['<key>']:
            with open(arg) as fd:
                algo, key, title = fd.read().strip().split(None, 2)
            key = "%s %s" % (algo, key)
            print("Adding deploy key %s" % arg)
            # repo.create_key(title=title, key=key, read_only=opts['--read-only'])
            data = {'title': title, 'key': key, 'read_only': opts['--read-only']}
            repo._post(url, data=data)

    @command
    def add_hook(self, opts):
        """<name> [<setting>...]
           Add a repository hook"""
        repo = self.repository(opts)
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
    def apply_pr(self, opts):
        """[--ssh|--http|--git] <pr-number>
           Applies a pull request as a series of cherry-picks"""
        repo = self.repository(opts)
        pr = repo.pull_request(opts['<pr-number>'])
        if not pr:
            err("Pull request %s does not exist" % opts['<pr-number>'])
        print("Applying PR#%d from %s: %s" % (pr.number, self.gh.user(pr.user).name, pr.title))
        # Warnings
        warned = False
        cbr = self.gitm('rev-parse', '--symbolic-full-name', 'HEAD').stdout.strip().replace('refs/heads/','')
        if cbr != pr.base.ref:
            print(wrap("Pull request was filed against %s, but you're on the %s branch" % (pr.base.ref, cbr), fgcolor.red))
            warned = True
        if pr.merged_at:
            print(wrap("Pull request was already merged at %s by %s" % (pr.merged_at, pr.merged_by), fgcolor.red))
        if not pr.mergeable or pr.mergeable_state != 'clean':
            print(wrap("Pull request will not apply cleanly", fgcolor.red))
            warned = True
        if pr.state == 'closed':
            print(wrap("Pull request has already been closed", fgcolor.red))
            warned = True
        if warned:
            if not self.question("Continue?", default=False):
                sys.exit(1)
        # Fetch PR if needed
        sha = self.git('rev-parse', '--verify', 'refs/pull/%d/head' % pr.number).stdout.strip()
        if sha != pr.head.sha:
            print("Fetching pull request")
            url = self.clone_url(self.gh.repository(pr.repository[0].replace('repos/', ''), pr.repository[1]), opts)
            self.gitm('fetch', url, 'refs/pull/%d/head:refs/pull/%d/head' % (pr.number, pr.number), redirect=False)
        head_sha = self.gitm('rev-parse', 'HEAD').stdout.strip()
        if self.git('merge-base', pr.head.sha, head_sha).stdout.strip() == head_sha:
            print("Fast-forward merging %d commit(s): %s..refs/pull/%d/head" % (pr.commits, pr.base.ref, pr.number))
            self.gitm('merge', '--ff-only', 'refs/pull/%d/head' % pr.number, redirect=False)
        else:
            print("Cherry-picking %d commit(s): %s..refs/pull/%d/head" % (pr.commits, pr.base.ref, pr.number))
            self.gitm('cherry-pick', '%s..refs/pull/%d/head' % (pr.base.ref, pr.number), redirect=False)

    @command
    @wants_parent
    def add_remote(self, opts):
        """[--ssh|--http|--git] <user> [<name>]
           Add user's fork as a named remote. The name defaults to the user's loginname"""
        for fork in self.repository(opts).iter_forks():
            if fork.owner.login in opts['<user>']:
                url = self.clone_url(fork, opts)
                name = opts['<name>'] or fork.owner.login
                self.gitm('remote', 'add', '-f', name, url, redirect=False)

    @command
    def add_public_keys(self, opts):
        """[<key>...]
           Adds keys to your public keys"""
        if not opts['<key>']:
            opts['<key>'] = glob.glob(os.path.join(os.path.expanduser('~'), '.ssh', 'id_*.pub'))
        existing = [x.key for x in self.gh.iter_keys()]
        for arg in opts['<key>']:
            with open(arg) as fd:
                algo, key, title = fd.read().strip().split(None, 2)
            key = "%s %s" % (algo, key)
            if key in existing:
                continue
            print("Adding %s" % arg)
            self.gh.create_key(title=title, key=key)

    @command
    def browse(self, opts):
        """[--parent] [<repo>] [<section>]
           Open the GitHub page for a repository in a browser"""
        sections = ['issues', 'pulls', 'wiki', 'branches', 'releases', 'contributors', 'graphs', 'settings']
        if opts['<repo>'] in sections and not opts['<section>']:
            opts['<repo>'], opts['<section>'] = None, opts['<repo>']
        repo = self.repository(opts)
        url = repo.html_url
        if opts['<section>']:
            url += '/' + opts['<section>']
        webbrowser.open_new(url)

    @command
    def calendar(self, opts):
        """[<user>]
           Show a timeline of a user's activity"""
        user = (opts['<user>'] or [self.my_login])[0]
        months = []
        rows = [[],[],[],[],[],[],[]]
        commits = []

        data = requests.get('https://github.com/users/%s/contributions' % user).text
        # Sorry, zalgo!
        data = re.findall(r'data-count="(.*?)" data-date="(.*?)"', data)
        y, m, d = [int(x) for x in data[0][1].split('-')]
        wd = (datetime.date(y,m,d).weekday()+1) % 7
        for i in range(wd):
            rows[i].append((None,None))
        if wd:
            months.append(m)
        for (count, date) in data:
            count = int(count)
            y, m, d = [int(x) for x in date.split('-')]
            wd = (datetime.date(y,m,d).weekday()+1) % 7
            rows[wd].append((d, count))
            if not wd:
                months.append(m)
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
           Display the contents of a file on GitHub"""
        for arg in opts['<file>']:
            repo, ref, file = ([None, None] + arg.split(':',2))[-3:]
            user = None
            if repo:
                user, repo = ([None] + repo.split('/'))[-2:]
                repo = self.gh.repository(user or self.my_login, repo)
            else:
                repo = self.repository(opts)
                file = self.rel2root(file)
            if '/' in file:
                dir, file = file.rsplit('/', 1)
            else:
                dir = ''
            content = repo.contents(path=dir, ref=ref or repo.default_branch)
            if not content or file not in content:
                err("No such file: %s" % arg)
            if content[file].type != 'file':
                err("Not a regular file: %s" % arg)
            resp = self.gh._session.get(content[file]._json_data['download_url'], stream=True)
            for chunk in resp.iter_content(4096):
                os.write(sys.stdout.fileno(), chunk)

    @command
    def check_pages(self, opts):
        """[<repo>] [--parent]
           Check the github pages configuration and content of your repo"""
        repo = self.repository(opts)

        if opts['<repo>']:
            self.clone(opts)
            os.chdir(repo.name)

        def warning(msg, url=None):
            print(wrap(msg, fgcolor.yellow))
            if url:
                print(wrap(url, attr.faint))

        def error(msg, url=None):
            print(wrap(msg, fgcolor.red))
            if url:
                print(wrap(url, attr.faint))

        # Old-style $user.github.com repos
        if repo.name.lower() == repo.owner.login.lower() + '.github.com':
            warning("Your repository is named %s.github.com, but should be named %s.github.io" % (repo.owner.login, repo.owner.login),
                    "https://help.github.com/articles/user-organization-and-project-pages/#user--organization-pages")

#        if repo.name.lower() == repo.owner.login.lower() + '.github.io' and repo.name != repo.name.lower():
#            error("You should not have capital letters in your repository name, please rename it from %s to %s" % (repo.name, repo.name.lower()))

        # Which branch do we check?
        if repo.name.lower() in (repo.owner.login.lower() + '.github.com', repo.owner.login.lower() + '.github.io'):
            branchname = 'master'
        else:
            branchname = 'gh-pages'

        # Do we have local changes?
        if self.git('rev-parse', '--symbolic-full-name', 'HEAD').stdout.strip() == 'refs/heads/%s' % branchname and self.git('status', '--porcelain').stdout.strip():
            warning("You have uncommitted changes. This tool checks the latest commit, not the working tree")

        # Do we have a pages branch?
        local = remote_tracking = remote = None

        output = self.git('ls-remote', repo.remote or 'origin', 'refs/heads/%s' % branchname).stdout
        for line in output.splitlines():
            remote = line.split()[0]
        if not remote:
            error("You have no %s branch on GitHub" % branchname,
                  "https://help.github.com/articles/user-organization-and-project-pages/")

        output = self.git('for-each-ref', '--format=%(refname) %(objectname) %(upstream:trackshort)',
                          'refs/remotes/%s/%s' % (repo.remote or 'origin', branchname),
                          'refs/heads/%s' % branchname,).stdout
        for line in output.splitlines():
            if line.startswith('refs/heads'):
                ref, sha, ahead = line.split()
                local = sha
                if ahead == '<':
                    warning("Your local %s branch is behind the one on GitHub" % branchname)
                elif ahead == '>':
                    warning("Your local %s branch is ahead of the one on GitHub" % branchname)
                elif ahead == '<>':
                    warning("Your local %s branch has diverged from the one on GitHub" % branchname)
            elif line.startswith('refs/remotes'):
                ref, sha = line.split()
                remote_tracking = sha
                if remote != remote_tracking:
                    warning("You need to fetch %s from GitHub to get its latest revision" % branchname)

        if not local or not remote_tracking:
            warning("You have no %s branch locally" % branchname,
                    "https://help.github.com/articles/user-organization-and-project-pages/")

        if local:
            ref = 'refs/heads/%s' % branchname
        elif remote_tracking:
            ref = 'refs/remotes/%s/%s' % (repo.remote, branchname)
        files = self.git('ls-tree', '-r', '--name-only', ref).stdout.splitlines()

        # Do we have an index.html
        if 'index.html' not in files:
            warning("You have no index.html")

        # Do we need .nojekyll (dirs starting with underscores)
        if '.nojekyll' not in files and '_config.yml' not in files:
            for file in files:
                if file.startswith('_'):
                    warning("You have filenames starting with underscores, but no .nojekyll file",
                            "https://help.github.com/articles/using-jekyll-with-pages/#turning-jekyll-off")
                break

        # Do we have unverified emails
        if repo.owner.login == self.me.login:
            for mail in self.gh.iter_emails():
                if not mail['verified']:
                    error("Unverified %s email address: %s" % (mail['primary'] and 'primary' or 'secondary', mail['email']))

        # Do we have a custom CNAME. Check DNS (Use meta api for A records)
        for file in files:
            if file.lower() == 'cname':
                if file != 'CNAME':
                    error("The CNAME file must be named in all caps",
                          "https://help.github.com/articles/adding-a-cname-file-to-your-repository/")
                cname = self.git('--no-pager', 'show', '%s:%s' % (ref, file)).stdout.strip()
                pages_ips = self.gh.meta()['pages']
                try:
                    import publicsuffix
                except ImportError:
                    import gitspindle.public_suffix as publicsuffix
                expect_cname = publicsuffix.PublicSuffixList(publicsuffix.fetch()).get_public_suffix(cname) != cname
                try:
                    import dns
                    import dns.resolver
                    resolver = dns.resolver.Resolver()
                    answer = resolver.query(cname)
                    for rrset in answer.response.answer:
                        name = rrset.name.to_text().rstrip('.')
                        if name == cname:
                            for rr in rrset:
                                if rr.rdtype == dns.rdatatype.A and expect_cname:
                                    warning("You should use a CNAME record for non-apex domains",
                                            "https://help.github.com/articles/tips-for-configuring-a-cname-record-with-your-dns-provider/")
                                if rr.rdtype == dns.rdatatype.A and rr.address not in pages_ips:
                                    error("IP address %s is incorreect for a pages site, use only %s" % (rr.address, ', '.join(pages_ips)),
                                          "https://help.github.com/articles/tips-for-configuring-a-cname-record-with-your-dns-provider/")
                                if rr.rdtype == dns.rdatatype.CNAME and rr.target != '%s.github.io.' % repo.owner.login:
                                    error("CNAME %s -> %s is incorrect, should be %s -> %s" % (name, rr.target, name, '%s.github.io.' % repo.owner.login),
                                          "https://help.github.com/articles/tips-for-configuring-an-a-record-with-your-dns-provider/")
                except ImportError:
                    if hasattr(self.shell, 'dig'):
                        lines = self.shell.dig('+nocomment', '+nocmd', '+nostats', '+noquestion', cname).stdout.splitlines()
                        for line in lines:
                            rname, ttl, _, rtype, value = line.split(None, 4)
                            if rname.rstrip('.') == cname:
                                if rtype == 'A' and expect_cname:
                                    warning("You should use a CNAME record for non-apex domains",
                                            "https://help.github.com/articles/tips-for-configuring-a-cname-record-with-your-dns-provider/")
                                if rtype == 'A' and value not in pages_ips:
                                    error("IP address %s is incorreect for a pages site, use only %s" % (value, ', '.join(pages_ips)),
                                          "https://help.github.com/articles/tips-for-configuring-a-cname-record-with-your-dns-provider/")
                                if rtype == 'CNAME' and value != '%s.github.io.' % repo.owner.login:
                                    error("CNAME %s -> %s is incorrect, should be %s -> %s" % (rname, value, rname, '%s.github.io.' % repo.owner.login),
                                          "https://help.github.com/articles/tips-for-configuring-an-a-record-with-your-dns-provider/")
                    else:
                        error("Cannot check DNS settings. Please install dnspython or dig")
                break

    @command
    def clone(self, opts, repo=None):
        """[--ssh|--http|--git] [--triangular [--upstream-branch=<branch>]] [--parent] [git-clone-options] <repo> [<dir>]
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
        if repo.fork:
            os.chdir(dir)
            self.set_origin(opts, repo=repo)

    @command
    def collaborators(self, opts):
        """[<repo>]
           List collaborators of a repository"""
        repo = self.repository(opts)
        users = list(repo.iter_collaborators())
        users.sort(key = lambda user: user.login)
        for user in users:
            print(user.login)

    @command
    def create(self, opts):
        """[--private] [--org=<org>] [--description=<description>]
           Create a repository on github to push to"""
        root = self.gitm('rev-parse', '--show-toplevel').stdout.strip()
        name = os.path.basename(root)
        if opts['--org']:
            dest = self.gh.organization(opts['--org'])
            ns = opts['--org']
        else:
            dest = self.gh
            ns = self.my_login

        if name in [x.name for x in dest.iter_repos() if x.owner.login == ns]:
            err("Repository already exists")
        repo = dest.create_repo(name=name, description=opts['--description'] or "", private=opts['--private'])

        if 'origin' in self.remotes():
            print("Remote 'origin' already exists, adding the GitHub repository as 'github'")
            self.set_origin(opts, repo=repo, remote='github')
        else:
            self.set_origin(opts, repo=repo)

    @command
    def create_token(self, opts):
        """[--store]
           Create a personal access token that can be used for git operations"""
        password = getpass.getpass("GitHub password: ")
        scopes = ['repo']
        name = "Git on %s" % socket.gethostname()
        host = self.config('host')
        if host and host not in ('https://api.github.com', 'api.github.com'):
            if not host.startswith(('http://', 'https://')):
                host = 'https://' + host
            gh = github3.GitHubEnterprise(url=host)
        else:
            gh = github3.GitHub()
        gh.login(self.my_login, password, two_factor_callback=lambda: prompt_for_2fa(self.my_login))
        try:
            auth = gh.authorize(self.my_login, password, scopes, name, "http://git-scm.com")
        except github3.GitHubError:
            type, exc = sys.exc_info()[:2]
            dont_raise = False
            if hasattr(exc, 'response') and exc.response.status_code == 422:
                for error in exc.response.json()['errors']:
                    if error['resource'] == 'OauthAccess' and error['code'] == 'already_exists':
                        if os.getenv('DEBUG'):
                            for auth in gh.iter_authorizations():
                                if auth.app['name'] in (name, '%s (API)' % name):
                                    auth.delete()
                            auth = gh.authorize(self.my_login, password, scopes, name, "http://git-scm.com")
                            dont_raise=True
                        else:
                            err('An OAuth token for git on this host already exists. Please delete it on your setting page')
            if not dont_raise:
                raise
        if auth is None:
            err("Authentication failed")
        token = auth.token
        print("Your personal access token is: %s" % token)
        if opts['--store']:
            host = self.config('host') or 'github.com'
            Credential(protocol='https', host=host, username=self.my_login, password=token).approve()
            print("Your personal access token has been stored in the git credential helper")

    @command
    def deploy_keys(self, opts):
        """[<repo>]
           Lists all keys for a repo"""
        repo = self.repository(opts)
        for key in repo.iter_keys():
            ro = key._json_data['read_only'] and 'ro' or 'rw'
            print("%s %s (id: %s, %s)" % (key.key, key.title or '', key.id, ro))

    @command
    def edit_hook(self, opts):
        """<name> [<setting>...]
           Edit a hook"""
        for hook in self.repository(opts).iter_hooks():
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
    def fetch(self, opts):
        """[--ssh|--http|--git] <user> [<refspec>]
           Fetch refs from a user's fork"""
        for fork in self.repository(opts).iter_forks():
            if fork.owner.login in opts['<user>']:
                url = self.clone_url(fork, opts)
                refspec = opts['<refspec>'] or 'refs/heads/*'
                if ':' not in refspec:
                    if not refspec.startswith('refs/'):
                        refspec += ':' + 'refs/remotes/%s/' % fork.owner.login + refspec
                    else:
                        refspec += ':' + refspec.replace('refs/heads/', 'refs/remotes/%s/' % fork.owner.login)
                self.gitm('fetch', url, refspec, redirect=False)

    @command
    def fork(self, opts):
        """[--ssh|--http|--git] [--triangular [--upstream-branch=<branch>]] [<repo>]
           Fork a repo and clone it"""
        do_clone = bool(opts['<repo>'])
        repo = self.repository(opts)
        if repo.owner.login == self.my_login:
            err("You cannot fork your own repos")

        if isinstance(repo, github3.gists.Gist):
            for fork in repo.iter_forks():
                if fork.owner.login == self.my_login:
                    err("You already forked this gist as %s" % fork.html_url)
        else:
            if repo.name in [x.name for x in self.gh.iter_repos() if x.owner.login == self.my_login]:
                err("Repository already exists")

        my_clone = repo.create_fork()
        self.wait_for_repo(my_clone.owner.login, my_clone.name, opts)
        if do_clone:
            self.clone(opts, repo=my_clone)
        else:
            self.set_origin(opts, repo=my_clone)

    @command
    @wants_parent
    def forks(self, opts):
        """[<repo>]
           List all forks of this repository"""
        repo = self.repository(opts)
        print("[%s] %s" % (wrap(repo.owner.login, attr.bright), repo.html_url))
        for fork in repo.iter_forks():
            print("[%s] %s" % (fork.owner.login, fork.html_url))

    @command
    def gist(self, opts):
        """[--description=<description>] <file>...
           Create a new gist from files or stdin"""
        files = {}
        description = opts['--description'] or ''
        for f in opts['<file>']:
            if f == '-':
                files['stdout'] = {'content': sys.stdin.read()}
            else:
                if not os.path.exists(f):
                    err("No such file: %s" % f)
                with open(f) as fd:
                    files[os.path.basename(f)] = {'content': fd.read()}
        gist = self.gh.create_gist(description=description, files=files)
        print("Gist created at %s" % gist.html_url)

    @command
    def gists(self, opts):
        """[<user>]
           Show all gists for a user"""
        user = (opts['<user>'] or [self.gh.user().login])[0]
        for gist in self.gh.iter_gists(user):
            print("%s - %s" % (gist.html_url, gist.description))

    @command
    def hooks(self, opts):
        """\nShow hooks that have been enabled"""
        for hook in self.repository(opts).iter_hooks():
            print(wrap("%s (%s)" % (hook.name, ', '.join(hook.events)), attr.bright))
            for key, val in sorted(hook.config.items()):
                if val in (None, ''):
                    continue
                print("  %s: %s" % (key, val))

    @command
    def ignore(self, opts):
        """[<language>...]
           Show gitignore patterns for one or more languages"""
        lang = opts['<language>']
        if not lang:
            langs = sorted(self.gh.gitignore_templates(), key = lambda x: x.lower())
            print("Languages for which a gitignore template is available:\n  * " + "\n  * ".join(langs))
        else:
            for l in lang:
                print("# Ignore patterns for " + l)
                print(self.gh.gitignore_template(l).strip())

    @command
    def ip_addresses(self, opts):
        """[--git] [--hooks] [--importer] [--pages]
           Show the IP addresses for github.com services in CIDR format"""
        ip_addresses = self.gh.meta()
        for what in ('git', 'hooks', 'importer', 'pages'):
            if opts['--' + what]:
                print("\n".join(ip_addresses[what]))

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
            issue = repo.issue(issue_no)
            if issue:
                print(wrap(issue.title.encode(sys.stdout.encoding, errors='backslashreplace').decode(sys.stdout.encoding), attr.bright, attr.underline))
                print(issue.body.encode(sys.stdout.encoding, errors='backslashreplace').decode(sys.stdout.encoding))
                print(issue.pull_request and issue.pull_request['html_url'] or issue.html_url)
            else:
                print('No issue with id %s found in repository %s' % (issue_no, repo.full_name))
        if not opts['<issue>']:
            ext = ''
            template = self.find_template(repo, 'ISSUE_TEMPLATE')
            if template:
                if '.' in template[0]:
                    ext = template[0][template[0].rfind('.'):]
                body = template[1]
                extra = None
            else:
                body = ""
                extra = """Reporting an issue on %s/%s
Please describe the issue as clearly as possible. Lines starting with '#' will
be ignored, the first line will be used as title for the issue.""" % (repo.owner.login, repo.name)
            title, body = self.edit_msg(None, body, extra, 'ISSUE_EDITMSG' + ext)
            if not body:
                err("Empty issue message")

            try:
                issue = repo.create_issue(title=title, body=body)
                print("Issue %d created %s" % (issue.number, issue.html_url))
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
            repos = list(self.gh.iter_repos(type='all'))
        else:
            repos = [self.repository(opts)]
        for repo in repos:
            repo = (opts['--parent'] and self.parent_repo(repo)) or repo
            filters = dict([x.split('=', 1) for x in opts['<filter>']])
            try:
                issues = list(repo.iter_issues(**filters))
            except github3.GitHubError:
                _, err, _ = sys.exc_info()
                if err.code == 410:
                    if len(repos) == 1:
                        print(err.message)
                    continue
                else:
                    raise
            if not issues:
                continue
            print(wrap("Issues for %s/%s" % (repo.owner.login, repo.name), attr.bright))
            for issue in issues:
                url = issue.pull_request and issue.pull_request['html_url'] or issue.html_url
                print("[%d] %s %s" % (issue.number, issue.title.encode(sys.stdout.encoding, errors='backslashreplace').decode(sys.stdout.encoding), url))

    @command
    def log(self, opts):
        """[--type=<type>] [--count=<count>] [--verbose] [<what>]
           Display github log for yourself or other users. Or for an organisation or a repo"""
        logtype = 'user'
        count = int(opts['--count'] or 30)
        verbose = opts['--verbose']
        if not opts['<what>']:
            what = self.me
        else:
            if '/' in opts['<what>']:
                logtype = 'repo'
                user, repo = opts['<what>'].split('/', 1)
                if user == 'gist':
                    what = self.gh.gist(repo)
                    if not what:
                        err("Gist %s does not exist" % repo)
                else:
                    what = self.gh.repository(user, repo)
                    if not what:
                        err("Repository %s/%s does not exist" % (user, repo))
            else:
                what = self.gh.user(opts['<what>'])
                if what.type == 'Organization':
                    logtype = 'org'
                if not what:
                    err("User %s does not exist" % opts['<what>'])

        if not opts['--type']:
            events = [x for x in what.iter_events(number=count)]
        else:
            events = []
            etype = opts['--type'].lower() + 'event'
            for event in what.iter_events(number=-1):
                if event.type.lower() == etype:
                    events.append(event)
                    if len(events) == count:
                        break

        now = datetime.datetime.now()
        for event in reversed(events):
            ts = event.created_at
            if ts.year == now.year:
                if (ts.month, ts.day) == (now.month, now.day):
                    ts = wrap(ts.strftime("%H:%M"), attr.faint)
                    tss = '     '
                else:
                    ts = wrap(ts.strftime("%m/%d %H:%M"), attr.faint)
                    tss = '           '
            else:
                ts = wrap(ts.strftime("%Y/%m/%d %H:%M"), attr.faint)
                tss = '                '
            repo = '/'.join(event.repo)
            repo_ = ' (%s)' % repo
            if logtype != 'user':
                repo_ = ''
                ts += ' %s' % event.actor.login
            if event.type == 'CommitCommentEvent':
                print("%s commented on commit %s%s" % (ts, event.payload['comment'].commit_id[:7], repo_))
            elif event.type == 'CreateEvent':
                if event.payload['ref_type'] == 'repository':
                    print("%s created %s %s" % (ts, event.payload['ref_type'], repo))
                else:
                    print("%s created %s %s%s" % (ts, event.payload['ref_type'], event.payload['ref'], repo_))
            elif event.type == 'DeleteEvent':
                print("%s deleted %s %s%s" % (ts, event.payload['ref_type'], event.payload['ref'], repo_))
            elif event.type == 'DownloadEvent':
                print("%s created download %s (%s)" % (ts, event.payload['name'], event.payload['description']))
            elif event.type == 'FollowEvent':
                print("%s started following %s" % (ts, event.payload['target'].login))
            elif event.type == 'ForkEvent':
                print("%s forked %s to %s/%s" % (ts, repo, event.payload['forkee'].owner.login, event.payload['forkee'].name))
            elif event.type == 'ForkApplyEvent':
                print("%s applied %s to %s%s" % (ts, event.payload['after'][:7], event.payload['head'], repo_))
            elif event.type == 'GistEvent':
                print("%s %sd gist #%s" % (ts, event.payload['action'], event.payload['gist'].html_url))
            elif event.type == 'GollumEvent':
                pages = len(event.payload['pages'])
                print("%s updated %d wikipage%s%s" % (ts, pages, {1:''}.get(pages, 's'), repo_))
            elif event.type == 'IssueCommentEvent':
                print("%s commented on issue #%s%s" % (ts, event.payload['issue'].number, repo_))
                if verbose:
                    print("%s %s %s" % (tss, event.payload['issue'].title, event.payload['comment']._json_data['html_url']))
            elif event.type == 'IssuesEvent':
                print("%s %s issue #%s%s" % (ts, event.payload['action'], event.payload['issue'].number, repo_))
                if verbose:
                    print("%s %s %s" % (tss, event.payload['issue'].title, event.payload['issue'].html_url))
            elif event.type == 'MemberEvent':
                print("%s %s %s to %s" % (ts, event.payload['action'], event.payload['member'].login, repo))
            elif event.type == 'PublicEvent':
                print("%s made %s open source" % repo)
            elif event.type == 'PullRequestReviewCommentEvent':
                print("%s commented on a pull request for commit %s%s" % (ts, event.payload['comment'].commit_id[:7], repo_))
            elif event.type == 'PullRequestEvent':
                print("%s %s pull_request #%s%s" % (ts, event.payload['action'], event.payload['pull_request'].number, repo_))
                if verbose:
                    print("%s %s %s" % (tss, event.payload['pull_request'].title, event.payload['pull_request'].html_url))

            elif event.type == 'PushEvent':
                # Old push events have shas and not commits
                if 'commits' in event.payload:
                    commits = len(event.payload['commits'])
                else:
                    commits = len(event.payload['shas'])
                print("%s pushed %d commits to %s%s" % (ts, commits, event.payload['ref'][11:], repo_))
                if verbose:
                    shas = '%s...%s' % (event.payload['before'][:8], event.payload['head'][:8])
                    print("%s %s/%s/compare/%s" % (tss, self.me.html_url, event.repo[1], shas))
            elif event.type == 'ReleaseEvent':
                print("%s released %s" % (ts, event.payload['name']))
            elif event.type == 'StatusEvent':
                print("%s commit %s changed to %s" % (ts, event.payload['sha'][:7], event.payload['state']))
            elif event.type == 'TeamAddEvent':
                if 'user' in event.payload:
                    what = 'user'
                    name = isinstance(event.payload['user'], dict) and event.payload['user']['name'] or event.payload['user'].name
                else:
                    what = 'repository'
                    name = isinstance(event.payload['repository'], dict) and event.payload['repository']['name'] or event.payload['repository'].name
                    print("%s %s %s was added to team %s" % (ts, what, name, event.payload['team'].name))
            elif event.type == 'WatchEvent':
                print("%s %s watching %s" % (ts, event.payload['action'], repo))
            elif event.type == 'GistHistoryEvent':
                print("%s committed %s additions, %s deletions" % (ts, event.additions, event.deletions))
            else:
                print(wrap("Cannot display %s. Please file a bug at github.com/seveas/git-spindle\nincluding the following output:" % event.type, attr.bright))
                pprint(event.payload)

    @command
    def ls(self, opts):
        """[<dir>...]
           Display the contents of a directory on GitHub"""
        for arg in opts['<dir>'] or ['']:
            repo, ref, file = ([None, None] + arg.split(':',2))[-3:]
            user = None
            if repo:
                user, repo = ([None] + repo.split('/'))[-2:]
                repo = self.gh.repository(user or self.my_login, repo)
            else:
                repo = self.repository(opts)
                file = self.rel2root(file)
            content = repo.contents(path=file, ref=ref or repo.default_branch)
            if not content:
                err("No such directory: %s" % arg)
            if not isinstance(content, dict):
                err("Not a directory: %s" % arg)
            content = sorted(content.values(), key=lambda file: file.name)
            mt = max([len(file.type) for file in content])
            ms = max([len(str(file.size)) for file in content])
            fmt = "%%(type)-%ds %%(size)-%ds %%(sha).7s %%(path)s" % (mt, ms)
            for file in content:
                print(fmt % file._json_data)

    @command
    def mirror(self, opts):
        """[--ssh|--http|--git] [--goblet] [<repo>]
           Mirror a repository, or all repositories for a user"""
        if opts['<repo>'] and opts['<repo>'].endswith('/*'):
            user = opts['<repo>'].rsplit('/', 2)[-2]
            for repo in self.gh.iter_repos(type='all') if user == self.my_login else self.gh.iter_user_repos(user, type='all'):
                if repo.owner.login != self.my_login:
                    continue
                opts['<repo>'] = '%s/%s' % (user, repo)
                self.mirror(opts)
            for repo in self.gh.iter_gists(user):
                opts['<repo>'] = 'gist/%s' % repo.name
                self.mirror(opts)
            return
        repo = self.repository(opts)
        git_dir = repo.name + '.git'
        cur_dir = os.path.basename(os.path.abspath(os.getcwd()))
        if cur_dir != git_dir and not os.path.exists(git_dir):
            url = self.clone_url(repo, opts)
            self.gitm('clone', '--mirror', url, redirect=False)
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
            cwd = os.getcwd()
            os.chdir(git_dir)
            self.setup_goblet(opts)
            os.chdir(cwd)

    @command
    def network(self, opts):
        """[<level>]
           Create a graphviz graph of followers and forks"""
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
        people = {self.my_login: P(self.me)}
        for i in range(level):
            for login, person in list(people.items()):
                if person.done:
                    continue

                sys.stderr.write("Looking at user %s\n" % login)
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
                for repo in self.gh.iter_user_repos(login, type='owner'):
                    sys.stderr.write("Looking at repo %s\n" % repo.name)
                    if repo.fork:
                        if repo.owner.login not in people:
                            people[repo.owner.login] = P(repo.owner)
                        parent = self.parent_repo(repo)
                        person.rel_to[parent.owner.login].append('forked %s' % parent.name)
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
    def protect(self, opts):
        """[--enforcement-level=<level>] [--contexts=<contexts>] <branch>
           Protect a branch against deletions, force-pushes and failed status checks"""
        repo = self.repository(opts)
        repo.branch(opts['<branch>']).protect(enforcement_level=opts['--enforcement-level'], contexts=(opts['--contexts'] or '').split(','))

    @command
    def protected(self, opts):
        """\nList active branch protections"""
        repo = self.repository(opts)
        for branch in repo.iter_branches(protected=True):
            data = branch._json_data['protection']
            msg = branch.name
            if data['required_status_checks']['contexts'] and data['required_status_checks']['enforcement_level'] != 'off':
                msg += ' (%s must pass for %s)' % (','.join(data['required_status_checks']['contexts']), data['required_status_checks']['enforcement_level'])
            print(msg)

    @command
    def public_keys(self, opts):
        """[<user>]
           Lists all keys for a user"""
        user = opts['<user>'] and opts['<user>'][0] or self.my_login
        if self.my_login == user:
            keys = self.gh.iter_keys()
        else:
            keys = self.gh.user(user).iter_keys()
        for key in keys:
            print("%s %s" % (key.key, key.title or ''))

    @command
    def pull_request(self, opts):
        """[--issue=<issue>] [--yes] [<yours:theirs>]
           Opens a pull request to merge your branch to an upstream branch"""
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
        # Do they exist on github?
        srcb = repo.branch(src)
        if not srcb:
            if self.question("Branch %s does not exist in your GitHub repo, shall I push?" % src):
                self.gitm('push', '-u', repo.remote, src, redirect=False)
            else:
                err("Aborting")
        elif srcb and srcb.commit.sha != commit:
            # Have we diverged? Then there are commits that are reachable from the github branch but not local
            diverged = self.gitm('rev-list', srcb.commit.sha, '^' + commit)
            if diverged.stderr or diverged.stdout:
                if self.question("Branch %s has diverged from GitHub, shall I push and overwrite?" % src, default=False):
                    self.gitm('push', '--force', repo.remote, src, redirect=False)
                else:
                    err("Aborting")
            else:
                if self.question("Branch %s not up to date on github, but can be fast forwarded, shall I push?" % src):
                    self.gitm('push', repo.remote, src, redirect=False)
                else:
                    err("Aborting")

        dstb = parent.branch(dst)
        if not dstb:
            err("Branch %s does not exist in %s/%s" % (dst, parent.owner.login, parent.name))

        # Do we have the dst locally?
        for remote in self.gitm('remote').stdout.strip().split("\n"):
            url = self.gitm('config', 'remote.%s.url' % remote).stdout.strip()
            if url in [parent.git_url, parent.ssh_url, parent.clone_url]:
                if parent.private and url != parent.ssh_url:
                    err("You should configure %s/%s to fetch via ssh, it is a private repo" % (parent.owner.login, parent.name))
                self.gitm('fetch', remote, redirect=False)
                break
        else:
            err("You don't have %s/%s configured as a remote repository" % (parent.owner.login, parent.name))

        # How many commits?
        accept_empty_body = False
        commits = try_decode(self.gitm('log', '--pretty=%H', '%s/%s..%s' % (remote, dst, src)).stdout).strip().split()
        commits.reverse()
        if not commits:
            err("Your branch has no commits yet")
        # Are we turning an issue into a commit?
        if opts['--issue']:
            pull = parent.create_pull_from_issue(base=dst, head='%s:%s' % (repo.owner.login, src), issue=int(opts['--issue']))
            print("Pull request %d created %s" % (pull.number, pull.html_url))
            return

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

        ext = ''
        template = self.find_template(repo, 'PULL_REQUEST_TEMPLATE')
        if template:
            if '.' in template[0]:
                ext = template[0][template[0].rfind('.'):]
            body = template[1].rstrip() + '\n\n' + body

        extra = """Requesting a pull from %s/%s into %s/%s

Please enter a message to accompany your pull request. Lines starting
with '#' will be ignored, and an empty message aborts the request.""" % (repo.owner.login, src, parent.owner.login, dst)
        extra += "\n\n " + try_decode(self.gitm('shortlog', '%s/%s..%s' % (remote, dst, src)).stdout).strip()
        extra += "\n\n " + try_decode(self.gitm('diff', '--stat', '%s^..%s' % (commits[0], commits[-1])).stdout).strip()
        title, body = self.edit_msg(title, body, extra, 'PULL_REQUEST_EDIT_MSG' + ext)
        if not body and not accept_empty_body:
            err("No pull request message specified")

        try:
            pull = parent.create_pull(base=dst, head='%s:%s' % (repo.owner.login, src), title=title, body=body)
            print("Pull request %d created %s" % (pull.number, pull.html_url))
        except:
            filename = self.backup_message(title, body, 'pull-request-message-')
            err("Failed to create a pull request, the pull request text has been saved in %s" % filename)

    @command
    def readme(self, opts):
        """[<repo>]
           Get the README for a repository"""
        repo = self.repository(opts)
        readme = repo.readme()
        if readme:
            os.write(sys.stdout.fileno(), readme.decoded)
        else:
            err("No readme found")

    @command
    def release(self, opts):
        """[--draft] [--prerelease] <tag> [<releasename>]
           Create a release"""
        repo = self.repository(opts)
        tag = opts['<tag>']
        if tag.startswith('refs/tags/'):
            tag = tag[10:]
        name = opts['<releasename>'] or tag
        ref = 'refs/tags/' + tag
        ret = self.git('rev-parse', '--quiet', '--verify', ref + '^0')
        if not ret:
            err("Tag %s does not exist yet" % tag)
        sha = ret.stdout.strip()
        if not self.git('ls-remote', repo.remote, ref).stdout.strip():
            if self.question("Tag %s does not exist in your GitHub repo, shall I push?" % tag):
                self.gitm('push', repo.remote, '%s:%s' % (ref, ref), redirect=False)
        body = ''
        if self.git('cat-file', '-t', ref).stdout.strip() == 'tag':
            body = self.git('--no-pager', 'log', '-1', '--format=%B', ref).stdout
        extra = """Creating release %s based on tag %s
Please enter a text to accompany your release. Lines starting with '#'
will be ignored""" % (name, tag)
        body = self.edit_msg(None, body, extra, 'RELEASE_TEXT', split_title=False)
        release = repo.create_release(tag, target_commitish=sha, name=name, body=body, draft=opts['--draft'], prerelease=opts['--prerelease'])
        print("Release '%s' created %s" % (release.name, release.html_url))

    @command
    def releases(self, opts):
        """[<repo>]
           List all releases"""
        repo = self.repository(opts)
        for release in repo.iter_releases():
            status = []
            if release.draft:
                status.append('draft')
            if release.prerelease:
                status.append('prerelease')
            status = status and ' ' + wrap(','.join(status), attr.faint) or ''
            print("%s (%s)%s %s" % (release.name, release.tag_name, status, release.html_url))

    @command
    def remove_collaborator(self, opts):
        """<user>...
           Remove a user as collaborator """
        repo = self.repository(opts)
        for user in opts['<user>']:
            repo.remove_collaborator(user)

    @command
    def remove_deploy_key(self, opts):
        """<key>...
           Remove deploy key by id"""
        repo = self.repository(opts)
        for key in opts['<key>']:
            repo.delete_key(key)

    @command
    def remove_hook(self, opts):
        """<name>
           Remove a hook"""
        for hook in self.repository(opts).iter_hooks():
            if hook.name == opts['<name>']:
                hook.delete()

    @command
    def render(self, opts):
        """[--save=<outfile>] <file>
           Render a markdown document"""
        template = """<!DOCTYPE html>
<html>
  <head>
    <link type="text/css" rel="stylesheet" media="all" href="http://necolas.github.io/normalize.css/latest/normalize.css"></link>
    <link type="text/css" rel="stylesheet" media="all" href="http://seveas.github.io/git-spindle/_static/github.css"></link>
    <link type="text/css" rel="stylesheet" media="all" href="https://cdnjs.cloudflare.com/ajax/libs/octicons/2.0.2/octicons.css"></link>
  </head>
  <body>
    <div class="container">
      <div id="readme" class="boxed-group">
        <h3><span class="octicon octicon-book"></span> %s</h3>
        <article class="markdown-body">
          %s
        </article>
      </div>
    </div>
  </body>
</html>"""
        with open(opts['<file>'][0]) as fd:
            data = fd.read()
        rendered = github3.markdown(data)
        if isinstance(rendered, bytes):
            rendered = rendered.decode('utf-8')
        rendered = rendered.replace('user-content-', '')
        html = template % (os.path.basename(opts['<file>'][0]), rendered)
        if opts['--save']:
            with open(opts['--save'], 'w') as fd:
                fd.write(html)
        else:
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as fd:
                fd.write(html.encode('utf-8'))
                fd.close()
                webbrowser.open('file://' + fd.name)
                time.sleep(1)
                os.remove(fd.name)

    @command
    def repos(self, opts):
        """[--no-forks] [<user>]
           List all repos of a user, by default yours"""
        if opts['<user>']:
            repos = list(self.gh.iter_user_repos(opts['<user>'][0]))
        else:
            repos = list(self.gh.iter_repos(type='all'))
            opts['<user>'] = [self.my_login]
        if not repos:
            return
        maxlen = max([len(x.name) for x in repos])
        # XXX github3.py PR 193
        # maxstar = len(str(max([x.stargazers for x in repos])))
        maxstar = len(str(max([x._json_data['stargazers_count'] for x in repos])))
        maxfork = len(str(max([x.forks for x in repos])))
        maxwatch = len(str(max([x.watchers for x in repos])))
        # XXX github support request filed: watchers is actually stars
        #fmt = u"%%-%ds \u2605 %%-%ds \u25c9 %%-%ds \u2919 %%-%ds %%s" % (maxlen, maxstar, maxwatch, maxfork)
        fmt = u"%%-%ds \u2605 %%-%ds \u2919 %%-%ds %%s" % (maxlen, maxstar, maxfork)
        for repo in repos:
            color = [attr.normal]
            if repo.private:
                color.append(fgcolor.red)
            if repo.fork:
                if opts['--no-forks']:
                    continue
                color.append(attr.faint)
            name = repo.name
            if opts['<user>'][0] != repo.owner.login:
                name = '%s/%s' % (repo.owner.login, name)
            msg = wrap(fmt % (name, repo._json_data['stargazers_count'], repo.forks, repo.description), *color)
            if not PY3:
                msg = msg.encode('utf-8')
            print(msg)

    @command
    def say(self, opts):
        """[<msg>]
           Let the octocat speak to you"""
        msg = github3.octocat(opts['<msg>'] or None)
        if isinstance(msg, bytes):
            msg = msg.decode('utf-8')
        print(msg)


    @command
    @wants_parent
    def setup_goblet(self, opts):
        """\nSet up goblet config based on GitHub config"""
        repo = self.repository(opts)
        repo = self.parent_repo(repo) or repo
        owner = self.gh.user(repo.owner.login)
        self.gitm('config', 'goblet.owner-name', owner.name.encode('utf-8') or owner.login)
        if owner.email:
            self.gitm('config', 'goblet.owner-mail', owner.email.encode('utf-8'))
        self.gitm('config', 'goblet.git-url', repo.git_url)
        self.gitm('config', 'goblet.http-url', repo.clone_url)
        goblet_dir = os.path.join(self.gitm('rev-parse', '--git-dir').stdout.strip(), 'goblet')
        if not os.path.exists(goblet_dir):
            os.mkdir(goblet_dir, 0o777)
            os.chmod(goblet_dir, 0o777)

    @command
    def set_origin(self, opts, repo=None, remote='origin'):
        """[--ssh|--http|--git] [--triangular [--upstream-branch=<branch>]]
           Set the remote 'origin' to github.
           If this is a fork, set the remote 'upstream' to the parent"""
        if not repo:
            repo = self.repository(opts)
            # Is this mine? No? Do I have a clone?
            if repo.owner.login != self.my_login:
                my_repo = self.gh.repository(self.me, repo.name)
                if my_repo:
                    repo = my_repo

        url = self.clone_url(repo, opts)
        if self.git('config', 'remote.%s.url' % remote).stdout.strip() != url:
            print("Pointing %s to %s" % (remote, url))
            self.gitm('config', 'remote.%s.url' % remote, url)
        self.gitm('config', '--replace-all', 'remote.%s.fetch' % remote, '+refs/heads/*:refs/remotes/%s/*' % remote)

        if repo.fork:
            parent = self.parent_repo(repo)
            url = self.clone_url(parent, opts)
            if self.git('config', 'remote.upstream.url').stdout.strip() != url:
                print("Pointing upstream to %s" % url)
                self.gitm('config', 'remote.upstream.url', url)
            self.gitm('config', 'remote.upstream.fetch', '+refs/heads/*:refs/remotes/upstream/*')
        else:
            # If issues are enabled, fetch pull requests
            try:
                list(repo.iter_issues(number=1))
            except github3.GitHubError:
                pass
            else:
                self.gitm('config', '--add', 'remote.%s.fetch' % remote, '+refs/pull/*/head:refs/pull/*/head')

        if self.git('ls-remote', remote).stdout.strip():
            self.gitm('fetch', remote, redirect=False)
        if repo.fork:
            self.gitm('fetch', 'upstream', redirect=False)

        if remote != 'origin':
            return

        self.set_tracking_branches(remote, upstream="upstream", triangular=opts['--triangular'], upstream_branch=opts['--upstream-branch'])

    @command
    def status(self, opts):
        """\nDisplay current and historical GitHub service status"""
        api = github3.GitHubStatus()
        messages = api.messages()
        if not messages:
            messages = [api.last_message()]
        status = api.status()
        status.update({
            'body': 'Current status: %s' % status['status'],
            'created_on': status['last_updated'],
        })
        messages.insert(0, status)
        for message in reversed(messages):
            ts = time.strptime(message['created_on'], '%Y-%m-%dT%H:%M:%SZ')
            offset = time.timezone
            if time.daylight:
                offset = time.altzone
            color = {'good': fgcolor.green, 'minor': fgcolor.yellow, 'major': fgcolor.red}[message['status']]
            ts = datetime.datetime(ts.tm_year, ts.tm_mon, ts.tm_mday, ts.tm_hour, ts.tm_min, ts.tm_sec) - datetime.timedelta(0,offset)
            print('%s %s %s' % (wrap(ts.strftime('%Y-%m-%d %H:%M'), attr.faint), wrap("%-5s" % message['status'], color), message['body']))

    @command
    def unprotect(self, opts):
        """ <branch>
           Remove branch protections from a branch"""
        repo = self.repository(opts)
        repo.branch(opts['<branch>']).unprotect()

    @command
    def whoami(self, opts):
        """\nDisplay GitHub user info"""
        opts['<user>'] = [self.my_login]
        self.whois(opts)

    @command
    def whois(self, opts):
        """<user>...
           Display GitHub user info"""
        for user_ in opts['<user>']:
            user = self.gh.user(user_)
            if not user:
                print("No such user: %s" % user_)
                continue
            emails = {}
            if user.login == self.my_login:
                for email in self.gh.iter_emails():
                    emails[email['email']] = email
            print(wrap(user.name or user.login, attr.bright, attr.underline))
            print('Profile   %s' % user.html_url)
            if user.email:
                unverified = ''
                if not emails.get(user.email, {}).get('verified', True):
                    unverified = ' ' + wrap('(not verified)', fgcolor.red, attr.bright)
                print('Email     %s%s' % (user.email, unverified))
                for email in emails:
                    if email == user.email:
                        continue
                    unverified = ''
                    if not emails[email]['verified']:
                        unverified = ' ' + wrap('(not verified)', fgcolor.red, attr.bright)
                    print('          %s%s' % (email, unverified))
            if user.blog:
                print('Blog      %s' % user.blog)
            if user.location:
                print('Location  %s' % user.location)
            if user.company:
                print('Company   %s' % user.company)
            print('Repos     %d public, %d private' % (user.public_repos, user.total_private_repos))
            print('Gists     %d public, %d private' % (user.public_gists, user.total_private_gists))
            if user.login == self.my_login:
                keys = self.gh.iter_keys()
            else:
                keys = user.iter_keys()
            for pkey in keys:
                algo, key = pkey.key.split()[:2]
                algo = algo[4:].upper()
                if pkey.title:
                    print("%s key%s...%s (%s)" % (algo, ' ' * (6 - len(algo)), key[-10:], pkey.title))
                else:
                    print("%s key%s...%s" % (algo, ' ' * (6 - len(algo)), key[-10:]))
            if user.login == self.my_login:
                orgs = self.gh.iter_orgs()
            else:
                orgs = list(user.iter_orgs())
            if orgs:
                print("Member of %s" % ', '.join([x.login for x in orgs]))
            if user.type == 'Organization':
                print('Members:')
                for member in self.gh.organization(user.login).iter_members():
                    print(" - %s" % member.login)

def prompt_for_2fa(user, cache={}):
    """Callback for github3.py's 2FA support."""
    if cache.get(user, (0,))[0] < time.time() - 30:
        code = raw_input("Two-Factor Authentication Code: ").strip()
        cache[user] = (time.time(), code)
    return cache[user][1]
