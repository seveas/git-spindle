import json
from operator import attrgetter
import requests
import uritemplate

def check(resp):
    if resp.status_code not in (200, 201, 204):
        try:
            message = resp.json()['error']['message']
        except (KeyError, ValueError):
            message = resp.content

        if resp.status_code == 401:
            raise BitBucketAuthenticationError(message)
        raise BitBucketError(message)
    if not resp.content:
        return None
    return resp.json()

class Bitbucket(object):
    def __init__(self, username, passwd):
        self.username = username
        self.passwd = passwd

    def user(self, username):
        return User(self, username=username)

    def repository(self, owner, slug):
        if isinstance(owner, BBobject):
            owner = owner.username
        return Repository(self, owner=owner, slug=slug)

class BitBucketError(Exception):
    pass

class BitBucketAuthenticationError(BitBucketError):
    pass

class BBobject(object):
    spindle = 'bitbucket'
    def __new__(cls, *args, **kwargs):
        self = super(BBobject, cls).__new__(cls)
        if not isinstance(self.uri, tuple):
            self.uri = (self.uri,)
        return self

    def __init__(self, bb, mode='fetch', **kwargs):
        self.bb = bb
        if mode:
            self.url = [uritemplate.expand(x, **kwargs) for x in self.uri]
        self.data = {}
        if mode == 'fetch':
            for arg in kwargs:
                setattr(self, arg, kwargs[arg])
            self.data = {}
            for url in self.url:
                self.data.update(self.get(url))
        elif mode == 'list':
            self.instances = []
            for instance in self.get(self.url[0]):
                kw = kwargs.copy()
                kw.update(instance)
                instance = type(self)(self.bb, mode=None, **kw)
                instance.url = [uritemplate.expand(x, **kw) for x in instance.uri]
                self.instances.append(instance)
        else:
            self.data = kwargs
        for datum in self.data:
            if datum == 'data':
                setattr(self, '_' + datum, self.data[datum])
            else:
                setattr(self, datum, self.data[datum])

    @classmethod
    def list(klass, bb, **kwargs):
        return klass(bb, mode="list", **kwargs).instances

    def get(self, *args, **kwargs):
        kwargs.update({'auth': (self.bb.username, self.bb.passwd)})
        return check(requests.get(*args, **kwargs))

    def post(self, *args, **kwargs):
        kwargs.update({'auth': (self.bb.username, self.bb.passwd)})
        return check(requests.post(*args, **kwargs))

    def put(self, *args, **kwargs):
        kwargs.update({'auth': (self.bb.username, self.bb.passwd)})
        return check(requests.put(*args, **kwargs))

    def delete_(self, *args, **kwargs):
        kwargs.update({'auth': (self.bb.username, self.bb.passwd)})
        return check(requests.delete(*args, **kwargs))

class User(BBobject):
    uri = 'https://bitbucket.org/api/2.0/users/{username}'

    def __eq__(self, other):
        if isinstance(other, str):
            return other == self.username
        if isinstance(other, dict):
            return other.get('username', None) == self.username
        return super(User, self).__eq__(other)

    def repository(self, slug):
        return Repository(self.bb, owner=self.username, slug=slug)

    def create_repository(self, slug, description, is_private, has_issues, has_wiki):
        data = {'owner': self.username, 'slug': slug, 'description': description, 'is_private': is_private,
                'scm': 'git', 'has_issues': has_issues, 'has_wiki': has_wiki}
        repo = self.post(uritemplate.expand(Repository.uri[1], slug=slug, owner=self.username), data=json.dumps(data), headers={'content-type': 'application/json'})
        return Repository(self.bb, mode=None, **repo)

    def create_key(self, key, label):
        url = uritemplate.expand(Key.uri, user=self.username)
        data = self.post(url, data={'user': self.username, 'key': key, 'label': label})
        return Key(self.bb, mode=None, **data)

    def keys(self):
        return Key.list(self.bb, user=self.username)

    def repositories(self):
        url = uritemplate.expand('https://bitbucket.org/api/2.0/repositories/{owner}', owner=self.username)
        data = self.get(url)['values']
        return [Repository(self.bb, mode=None, **repo) for repo in data]

    def snippets(self):
        url = uritemplate.expand('https://bitbucket.org/api/2.0/snippets/{owner}', owner=self.username)
        data = self.get(url)['values']
        return [Snippet(self.bb, mode=None, **snippet) for snippet in data]

    def create_snippet(self, description, files):
        url = uritemplate.expand('https://bitbucket.org/api/2.0/snippets/{owner}', owner=self.username)
        data = {'scm': 'git', 'is_private': 'false', 'title': description}
        files = [('file', (filename, content)) for (filename, content) in files.items()]
        snippet = self.post(url, data=data, files=files)
        return Snippet(self.bb, mode=None, **snippet)

    def emails(self):
        url = uritemplate.expand('https://bitbucket.org/api/1.0/users/{username}/emails', username=self.username)
        return self.get(url)

def ssh_fix(url):
    if not url.startswith('ssh://'):
        return url
    return ':'.join(url[6:].split('/',1))

class PullRequest(BBobject):
    uri = 'https://api.bitbucket.org/2.0/repositories/{owner}/{slug}/pullrequests/{id}'

class Repository(BBobject):
    uri = ('https://bitbucket.org/api/1.0/repositories/{owner}/{slug}',
           'https://bitbucket.org/api/2.0/repositories/{owner}/{slug}')

    def __init__(self, *args, **kwargs):
        super(Repository, self).__init__(*args, **kwargs)
        if not hasattr(self, 'links'):
            return
        links, self.links['clone'] = self.links['clone'], {}
        for link in links:
            self.links['clone'][link['name']] = ssh_fix(link['href'])

    def fork(self):
        self.post(self.url[0] + '/fork', data={'name': self.name})
        for _ in range(5):
            try:
                return self.bb.repository(self.bb.username, self.name)
            except BitBucketError:
                print("Waiting for repository to be forked...")

    def main_branch(self):
        return self.get(self.url[0] + '/main-branch')['name']

    def branches(self):
        branches = self.get(self.url[0] + '/branches')
        return dict([(key, Branch(self.bb, mode=None, repository=self, **val)) for (key, val) in branches.items()])

    def pull_requests(self, **params):
        url = 'https://bitbucket.org/api/2.0/repositories/%s/pullrequests?state=OPEN' % self.full_name
        data = self.get(url)['values']
        return [PullRequest(self.bb, mode=None, **pr) for pr in data]

    def pull_request(self, number):
        owner, slug = self.full_name.split('/')
        return PullRequest(self.bb, owner=owner, slug=slug, id=number)

    def create_pull_request(self, src, dst, title, body):
        data = {'title': title, 'description': body}
        data['source'] = {'branch': {'name': src.branch}, 'repository': {'full_name': src.repository.full_name}}
        data['destination'] = {'branch': {'name': dst.branch}}
        pr = self.post(self.url[1] + '/pullrequests', data=json.dumps(data), headers={'content-type': 'application/json'})
        return PullRequest(self.bb, mode=None, **pr)

    def forks(self):
        data = self.get(self.links['forks']['href'])['values']
        return [Repository(self.bb, mode=None, **repo) for repo in data]

    def issues(self, **params):
        url = 'https://bitbucket.org/api/1.0/repositories/%s/issues' % self.full_name
        data = self.get(url, data=params)['issues']
        return [Issue(self.bb, mode=None, **issue) for issue in data]

    def issue(self, id):
        return Issue(self.bb, owner=self.owner['username'], slug=self.slug, id=id, repo=self)

    def create_issue(self, title, body):
        data = {'title': title, 'content': body}
        issue = self.post(self.url[0] + '/issues', data=data)
        issue['repo'] = self
        return Issue(self.bb, mode=None, **issue)

    def src(self, revision, path):
        return Source(self.bb, owner=self.owner['username'], slug=self.slug, revision=revision, path=path.split('/'))

    def delete(self):
        if not hasattr(self, 'url'):
            data = {'owner': self.owner['username'], 'slug': self.name}
            self.url = [uritemplate.expand(x, **data) for x in self.uri]
        return self.delete_(self.url[1])

    def add_privilege(self, user, priv):
        data = {'owner': self.owner['username'], 'slug': self.name, 'user': user}
        url = uritemplate.expand('https://bitbucket.org/api/1.0/privileges/{owner}/{slug}/{user}', data)
        return self.put(url, data=priv)

    def remove_privilege(self, user):
        data = {'owner': self.owner['username'], 'slug': self.name, 'user': user}
        url = uritemplate.expand('https://bitbucket.org/api/1.0/privileges/{owner}/{slug}/{user}', data)
        return self.delete_(url)

    def privileges(self):
        data = {'owner': self.owner['username'], 'slug': self.name}
        url = uritemplate.expand('https://bitbucket.org/api/1.0/privileges/{owner}/{slug}', data)
        return self.get(url)

    def add_deploy_key(self, key, label):
        url = self.url[0] + '/deploy-keys'
        return self.post(url, {'key': key, 'label': label})

    def remove_deploy_key(self, key):
        url = self.url[0] + '/deploy-keys/' + key
        return self.delete_(url)

    def deploy_keys(self):
        url = self.url[0] + '/deploy-keys'
        return self.get(url)

    def invite(self, email, priv):
        data = {'owner': self.owner['username'], 'slug': self.name, 'email': email}
        url = uritemplate.expand('https://bitbucket.org/api/1.0/invitations/{owner}/{slug}/{+email}', data)
        return self.post(url, {'permission': priv})

class Branch(BBobject):
    uri = None

class Key(BBobject):
    uri = 'https://bitbucket.org/api/1.0/users/{user}/ssh-keys'

    def delete(self):
        if not hasattr(self, 'url'):
            self.url = [uritemplate.expand(x, user=self.owner['username']) for x in self.uri]
        self.delete_(self.url[0] + '/%d' % self.pk)

class Issue(BBobject):
    uri = 'https://bitbucket.org/api/1.0/repositories/{owner}/{slug}/issues/{id}'

    def get_url(self):
        return 'https://bitbucket.org/%s/%s/issue/%s/' % (self.repo.owner['username'], self.repo.slug, self.local_id)

    html_url = property(get_url)

class Source(BBobject):
    uri = 'https://bitbucket.org/api/1.0/repositories/{owner}/{slug}/src/{revision}{/path*}'

class Snippet(BBobject):
    uri = 'https://bitbucket.org/api/2.0/snippets/{owner}/{id}'

    def __init__(self, *args, **kwargs):
        super(Snippet, self).__init__(*args, **kwargs)
        if not hasattr(self, 'links'):
            return
        links, self.links['clone'] = self.links['clone'], {}
        for link in links:
            self.links['clone'][link['name']] = ssh_fix(link['href'])

    def delete(self):
        if not hasattr(self, 'url'):
            data = {'owner': self.owner['username'], 'id': self.id}
            self.url = [uritemplate.expand(x, **data) for x in self.uri]
        return self.delete_(self.url[0])
