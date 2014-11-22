# Monkeypatch github3.gists.Gist to behave more like a repo

import github3.gists
import github3.repos

github3.gists.Gist.spindle = 'github'
github3.repos.Repository.spindle = 'github'

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

import gitspindle.glapi as glapi
glapi.Project.spindle = 'gitlab'
glapi.UserProject.spindle = 'gitlab'
