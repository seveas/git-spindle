from gitspindle import *
from gitspindle.ansi import *
import gitspindle.glapi as glapi
import base64
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

    def parent_repo(self, repo):
       if getattr(repo, 'forked_from_project', False):
           return self.gl.Project(repo.forked_from_project['id'])

    def find_repo(self, user, name):
        try:
            for repo in self.gl.search_projects(name):
                if repo.name == name and hasattr(repo, 'owner') and repo.owner.username == user:
                    return repo
        except glapi.GitlabListError:
            pass

    def find_user(self, username):
        try:
            for user in self.gl.User(search=username):
                if user.username == username:
                    return user
        except glapi.GitlabListError:
            pass

    def profile_url(self, user):
        return 'https://gitlab.com/u/%s' % user.username

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
            url = repo.http_url_to_repo
            if opts['--ssh'] or not repo.public:
                url = repo.ssh_url_to_repo
            self.gitm('remote', 'add', user, url)
            self.gitm('config', 'remote.%s.gitlab-id' % user, repo.id)
            self.gitm('fetch', user, redirect=False)

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
        """[--ssh|--http] [--parent] <repo>
           Clone a repository by name"""
        repo = opts['remotes']['.dwim']
        url = repo.ssh_url_to_repo
        if repo.owner.username != self.me.username:
            url = repo.http_url_to_repo
        if opts['--ssh'] or not repo.public:
            url = repo.ssh_url_to_repo
        elif opts['--http']:
            url = repo.http_url_ro_repo

        self.gitm('clone', url, repo.name, redirect=False).returncode
        self.gitm('config', 'remote.origin.gitlab-id', repo.id, cwd=repo.name)
        if hasattr(repo, 'forked_from_project'):
            os.chdir(repo.name)
            self.set_origin(opts)
            self.gitm('fetch', 'upstream', redirect=False)

    @command
    @needs_repo
    def create(self, opts):
        """[--private|--internal] [-d <description>]
           Create a repository on github to push to"""
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

        if self.git('config', 'remote.origin.url').stdout.strip() != repo.ssh_url_to_repo:
            print("Pointing origin to %s" % repo.ssh_url_to_repo)
            self.gitm('config', 'remote.origin.url', repo.ssh_url_to_repo)
            self.gitm('config', 'remote.origin.gitlab-id', repo.id)
            self.gitm('fetch', 'origin', redirect=False)

        parent = self.parent_repo(repo)
        if parent:
            url = parent.http_url_to_repo
            if opts['--ssh'] or not parent.public:
                url = parent.ssh_url_to_repo
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
        """[<user>...]
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
