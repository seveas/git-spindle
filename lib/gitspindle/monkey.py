# Set the spindle attribute
import github3.gists

# Monkeypatch github3.gists.Gist to behave more like a repo
github3.gists.gist._Gist.ssh_url = property(lambda self: 'git@gist.github.com:/%s.git' % self.id)
github3.gists.gist._Gist.clone_url = property(lambda self: self.git_pull_url)
github3.gists.gist._Gist.git_url = property(lambda self: 'git://gist.github.com/%s.git' % self.id)
github3.gists.gist._Gist.name = property(lambda self: self.id)
github3.gists.gist._Gist.private = property(lambda self: not self.public)
github3.gists.gist._Gist.create_fork = github3.gists.Gist.fork
# XXX - There is nothing in the API output that indicates forkedness
github3.gists.gist._Gist.fork = False
github3.gists.gist._Gist.issues = lambda self, *args, **kwargs: []
def _gist_events(self, number=300):
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
github3.gists.Gist.events = _gist_events
class Content(object):
    def __init__(self, file):
        self.decoded = file.content()
def _gist_contents(self, path, ref):
    # XXX ignore ref for now, can't do much with it
    for f in self.files():
        if f.filename == path:
            return Content(f)
github3.gists.Gist.file_contents = _gist_contents

# This is needed when working with the device authentication flow, as we're
# getting fewer attributes back
import github3.users
github3.users.AuthenticatedUser._update_attributes = github3.users.User._update_attributes

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
