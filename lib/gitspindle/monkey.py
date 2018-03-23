# Set the spindle attribute
import github3.gists
import github3.repos
github3.gists.Gist.spindle = 'github'
github3.repos.Repository.spindle = 'github'
import gitspindle.glapi as glapi
glapi.Project.spindle = 'gitlab'
glapi.UserProject.spindle = 'gitlab'

# Monkeypatch github3.gists.Gist to behave more like a repo
github3.gists.Gist.ssh_url = property(lambda self: 'git@gist.github.com:/%s.git' % self.id)
github3.gists.Gist.clone_url = property(lambda self: self.git_pull_url)
github3.gists.Gist.git_url = property(lambda self: 'git://gist.github.com/%s.git' % self.id)
github3.gists.Gist.name = property(lambda self: self.id)
github3.gists.Gist.private = property(lambda self: not self.public)
github3.gists.Gist.create_fork = github3.gists.Gist.fork
# XXX - There is nothing in the API output that indicates forkedness
github3.gists.Gist.fork = False
github3.gists.Gist.iter_issues = lambda self, *args, **kwargs: []
def _iter_gist_events(self, number=300):
    for event in self.history[:number]:
        yield GistEvent(event, self)
class GistEvent(object):
    type = 'GistHistoryEvent'
    def __init__(self, history, gist):
        self.created_at = history.committed_at
        self.additions = history.additions
        self.deletions = history.deletions
        self.actor = history.user
        if not self.actor.login:
            self.actor = gist.owner
        self.repo = ('gist', gist.name)
github3.gists.Gist.iter_events = _iter_gist_events
class Content(object):
    def __init__(self, file):
        self.decoded = file.content
def _gist_contents(self, path, ref):
    # XXX ignore ref for now, can't do much with it
    for f in self.iter_files():
        if f.filename == path:
            return Content(f)
github3.gists.Gist.contents = _gist_contents

# Monkeypatch github3.session.request to warn when approaching rate limits
from github3.session import GitHubSession

from gitspindle.ansi import wrap, fgcolor, attr
import time
warned = False
def request(self, *args, **kwargs):
    global warned
    r = self.orig_request(*args, **kwargs)
    # Warn when approaching the rate limit
    limit = int(r.headers.get('x-ratelimit-limit', 0))
    remaining = int(r.headers.get('x-ratelimit-remaining', 0))
    reset = int(r.headers.get('x-ratelimit-reset', 0))
    if limit and (remaining < 0.20 * limit) and not warned:
        msg = "You are approaching the API rate limit. Only %d/%d requests remain until %s" % (remaining, limit, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(reset)))
        print(wrap(msg, fgcolor.red, attr.bright))
        warned = True
    return r
GitHubSession.orig_request = GitHubSession.request
GitHubSession.request = request

# Add missing protect_branch / unprotect_branch methods
import json
from github3.decorators import requires_auth
def branch(self, name):
    url = self._build_url('branches', name, base_url=self._api)
    old_accept = self._session.headers.pop('Accept')
    self._session.headers['Accept'] = 'application/vnd.github.loki-preview+json'
    try:
        data = self._json(self._get(url), 200)
        if not data:
            return
        branch = github3.repos.branch.Branch(data)
        branch._session = self._session
        return branch
    finally:
        self._session.headers['Accept'] = old_accept

from github3.structs import GitHubIterator
def iter_branches(self, number=-1, etag=None, protected=False):
    url = self._build_url('branches', base_url=self._api)
    headers = {'Accept': 'application/vnd.github.loki-preview+json'}
    return GitHubIterator(int(number), url, github3.repos.branch.Branch, self, etag=etag, headers=headers, params={'protected': int(protected)})

@requires_auth
def protect(self, contexts=[], enforcement_level=None):
    data = {'enabled': True}
    if contexts or enforcement_level:
        data['required_status_checks'] = {'contexts': contexts, 'enforcement_level': enforcement_level or 'everyone'}
    old_accept = self._session.headers.pop('Accept')
    self._session.headers['Accept'] = 'application/vnd.github.loki-preview+json'
    try:
        return self._patch(self.links['self'], data=json.dumps({'protection': data}))
    finally:
        self._session.headers['Accept'] = old_accept

@requires_auth
def unprotect(self):
    old_accept = self._session.headers.pop('Accept')
    self._session.headers['Accept'] = 'application/vnd.github.loki-preview'
    try:
        return self._patch(self.links['self'], data=json.dumps({'protection': {'enabled': False}}))
    finally:
        self._session.headers['Accept'] = old_accept

github3.repos.repo.Repository.branch = branch
github3.repos.repo.Repository.iter_branches = iter_branches
github3.repos.branch.Branch.protect = protect
github3.repos.branch.Branch.unprotect = unprotect

# Monkeypatch docopt to support our git-clone-options-hack
import docopt
known_options = {
    'clone': (
        '-q', '--quiet', '-v', '--verbose', '-n', '--no-checkout', '--bare',
        '--mirror', '--reference=<repository>', '--progress', '-o <oname>', '--origin=<oname>',
        '-b <name>', '--branch=<name>', '-u <upload-pack>', '--upload-pack=<upload-pack>',
        '--template=<template-directory>', '-c <key-value>', '--config=<key-value>',
        '--depth=<depth>', '--single-branch', '--no-single-branch', '--recursive', '--recurse-submodules',
        '--separate-git-dir=<git_dir>'),
}

class GitOption(docopt.Option):
    def match(self, left, collected=None):
        if left and isinstance(left[0], docopt.Option) and ((self.short == left[0].short and self.short) or (self.long == left[0].long and self.long)):
            opt = left.pop(0)
            # Hijack the command argument to store the data
            cmd = [x for x in collected if type(x).__name__ == 'Command'][1]
            if not isinstance(cmd.value, list):
                cmd.value = []
            cmd.value.append(opt.short or opt.long)
            if opt.argcount:
                cmd.value.append(opt.value)
        return True, left, collected

    def __repr__(self):
        return 'Git' + super(GitOption, self).__repr__()


def parse_atom(tokens, options):
    if len(tokens) > 3 and (tokens[0], tokens[2]) == ('[', ']') and \
        tokens[1].startswith('git-') and tokens[1].endswith('-options'):
            token = tokens[1][4:-8]
            tokens.move(); tokens.move(); tokens.move()
            ret = []
            for opt in known_options[token]:
                opt = docopt.parse_pattern(opt, []).children[0]
                opt = GitOption(opt.short, opt.long, opt.argcount, opt.value)
                ret.append(opt)
                options.append(opt)
            return ret
    return docopt.orig_parse_atom(tokens, options)

docopt.orig_parse_atom = docopt.parse_atom
docopt.parse_atom = parse_atom

def formal_usage(printable_usage):
    usage = real_printable_usage(printable_usage).splitlines()
    ret = []
    for num, line in enumerate(usage):
        if line[0].isupper() and usage[num+1].startswith('  git'):
            continue
        ret.append(line)
    return docopt.orig_formal_usage('\n'.join(ret))
real_printable_usage = docopt.printable_usage
docopt.printable_usage = lambda x: x
docopt.orig_formal_usage = docopt.formal_usage
docopt.formal_usage = formal_usage
