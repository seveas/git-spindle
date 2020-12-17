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
    if not resp.headers['Content-Type'].startswith('application/json'):
        return resp.content
    return resp.json()

class Bitbucket(object):
    def __init__(self, username, passwd):
        self.username = username
        self.passwd = passwd

    def user(self, username=None):
        return User(self, username=username)

    def team(self, username):
        return Team(self, username=username)

    def workspace(self, workspace):
        return Workspace(self, workspace=workspace)

class BitBucketError(Exception):
    pass

class BitBucketAuthenticationError(BitBucketError):
    pass

class BBobject(object):
    def __new__(cls, *args, **kwargs):
        self = super(BBobject, cls).__new__(cls)
        return self

    def __init__(self, bb, mode='fetch', **kwargs):
        self.bb = bb
        self.data = {}
        if mode == 'fetch':
            for arg in kwargs:
                setattr(self, arg, kwargs[arg])
            self.url = kwargs.get('url', uritemplate.expand(self.uri, **kwargs)).replace('!api', 'api')
            self.data = self.get(self.url)
        elif mode == 'list':
            self.url = kwargs.get('url', uritemplate.expand(self.list_uri, **kwargs)).replace('!api', 'api')
            self.instances = []
            # FIXME properly handle pagination
            for instance in self.get(self.url)["values"]:
                kw = kwargs.copy()
                kw.update(instance)
                instance = type(self)(self.bb, mode=None, **kw)
                instance.url = instance.links['self']['href']
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
    uri = 'https://bitbucket.org/api/2.0/users/{id}'

    def __init__(self, bb, username):
        team = bb.team(username)
        super(User, self).__init__(bb, id=team.account_id)

    def __eq__(self, other):
        if isinstance(other, str):
            return other == self.account_id
        if isinstance(other, dict):
            return other.get('account_id', None) == self.account_id
        return super(User, self).__eq__(other)

    def repository(self, slug):
        return Repository(self.bb, owner=self.nickname, slug=slug)

    def create_repository(self, slug, description, is_private, has_issues, has_wiki):
        data = {'owner': self.nickname, 'slug': slug, 'description': description, 'is_private': is_private,
                'scm': 'git', 'has_issues': has_issues, 'has_wiki': has_wiki}
        repo = self.post(uritemplate.expand(Repository.uri, slug=slug, workspace=self.nickname), data=json.dumps(data), headers={'content-type': 'application/json'})
        repo['is_fork'] = False
        return Repository(self.bb, mode=None, **repo)

    def create_key(self, key, label):
        url = uritemplate.expand(Key.uri, user=self.account_id)
        data = self.post(url, data={'user': self.account_id, 'key': key, 'label': label})
        return Key(self.bb, mode=None, **data)

    def keys(self):
        return Key.list(self.bb, user=self.account_id)

    def repositories(self):
        url = 'https://bitbucket.org/api/2.0/repositories?role=member'
        data = self.get(url)['values']
        return [Repository(self.bb, mode=None, **entry) for entry in data]

    def snippets(self):
        url = 'https://bitbucket.org/api/2.0/snippets/'
        data = self.get(url)['values']
        return [Snippet(self.bb, mode=None, **snippet) for snippet in data]

    def create_snippet(self, description, files):
        url = 'https://bitbucket.org/api/2.0/snippets/'
        data = {'scm': 'git', 'is_private': 'false', 'title': description}
        files = [('file', (filename, content)) for (filename, content) in files.items()]
        snippet = self.post(url, data=data, files=files)
        return Snippet(self.bb, mode=None, **snippet)

class Team(BBobject):
    uri = 'https://bitbucket.org/api/2.0/teams/{username}'

def ssh_fix(url):
    if not url.startswith('ssh://'):
        return url
    return ':'.join(url[6:].split('/',1))

class PullRequest(BBobject):
    uri = 'https://api.bitbucket.org/2.0/repositories/{owner}/{slug}/pullrequests/{id}'

    def get_url(self):
        return self.links['html']['href']

    html_url = property(get_url)

class Repository(BBobject):
    uri = 'https://bitbucket.org/api/2.0/repositories/{workspace}/{slug}'
    list_uri = 'https://bitbucket.org/api/2.0/repositories/{workspace}/'

    def __init__(self, *args, **kwargs):
        self.parent = None
        super(Repository, self).__init__(*args, **kwargs)
        if not hasattr(self, 'links'):
            return
        links, self.links['clone'] = self.links['clone'], {}
        for link in links:
            self.links['clone'][link['name']] = ssh_fix(link['href'])


    def fork(self):
        self.post(self.url + '/forks', data={'name': self.name})
        for _ in range(5):
            try:
                return self.bb.workspace(self.bb.username).repository(self.name)
            except BitBucketError:
                print("Waiting for repository to be forked...")

    def branches(self):
        branches = self.get(self.url + '/refs')['values']
        return dict([(branch['name'], Branch(self.bb, mode=None, repository=self, **branch)) for branch in branches if branch['type'] == 'branch'])

    def pull_requests(self, **params):
        url = 'https://bitbucket.org/api/2.0/repositories/%s/pullrequests?state=OPEN' % self.full_name
        data = self.get(url)['values']
        return [PullRequest(self.bb, mode=None, **pr) for pr in data]

    def pull_request(self, number):
        owner, slug = self.full_name.split('/')
        return PullRequest(self.bb, owner=owner, slug=slug, id=number)

    def create_pull_request(self, src, dst, title, body):
        data = {'title': title, 'description': body}
        data['source'] = {'branch': {'name': src.name}, 'repository': {'full_name': src.repository.full_name}}
        data['destination'] = {'branch': {'name': dst.name}}
        pr = self.post(self.url + '/pullrequests', data=json.dumps(data), headers={'content-type': 'application/json'})
        return PullRequest(self.bb, mode=None, **pr)

    def forks(self):
        data = self.get(self.links['forks']['href'].replace('!api', 'api'))['values']
        return [Repository(self.bb, mode=None, **repo) for repo in data]

    def issues(self, **params):
        url = 'https://bitbucket.org/api/2.0/repositories/%s/issues' % self.full_name
        data = self.get(url, data=params)['values']
        return [Issue(self.bb, mode=None, **issue) for issue in data]

    def issue(self, id):
        return Issue(self.bb, owner=self.owner['nickname'], slug=self.slug, id=id, repo=self)

    def create_issue(self, title, body):
        data = {'title': title, 'content': body}
        issue = self.post(self.url + '/issues', data=json.dumps(data))
        issue['repo'] = self
        return Issue(self.bb, owner=self.owner['nickname'], slug=self.slug, id=issue['local_id'], repo=self)

    def src(self, revision, path):
        uri = 'https://bitbucket.org/api/2.0/repositories/{workspace}/{slug}/src/{node}/{path}'
        url = uritemplate.expand(uri, workspace=self.owner['nickname'], slug=self.slug, node=revision, path=path)
        data = self.get(url)
        if isinstance(data, bytes):
            return data
        return data['values']

    def delete(self):
        if not hasattr(self, 'url'):
            data = {'owner': self.owner['account_id'], 'slug': self.name}
            self.url = [uritemplate.expand(x, **data) for x in self.uri]
        return self.delete_(self.url[1])

    def permissions(self):
        data = {'workspace': self.owner['nickname'], 'slug': self.name}
        url = uritemplate.expand('https://bitbucket.org/api/2.0/workspaces/{workspace}/permissions/repositories/{slug}', data)
        return self.get(url)['values']

    def add_deploy_key(self, key, label):
        url = self.url + '/deploy-keys'
        return self.post(url, {'key': key, 'label': label})

    def remove_deploy_key(self, key):
        url = self.url + '/deploy-keys/' + key
        return self.delete_(url)

    def deploy_keys(self):
        url = self.url + '/deploy-keys'
        return self.get(url)['values']

class Branch(BBobject):
    pass

class Key(BBobject):
    uri = 'https://bitbucket.org/api/2.0/users/{user}/ssh-keys/{key_id}'
    list_uri = 'https://bitbucket.org/api/2.0/users/{user}/ssh-keys'

    def delete(self):
        if not hasattr(self, 'url'):
            self.url = [uritemplate.expand(x, user=self.owner['username']) for x in self.uri]
        self.delete_(self.url[0] + '/%d' % self.pk)

class Issue(BBobject):
    uri = 'https://bitbucket.org/api/2.0/repositories/{owner}/{slug}/issues/{id}'

    def get_url(self):
        return self.links['html']['href']

    html_url = property(get_url)

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

class Workspace(BBobject):
    uri = 'https://bitbucket.org/api/2.0/workspaces/{workspace}'
    repositories_uri = 'https://bitbucket.org/api/2.0/repositories?role=member'

    def repositories(self):
        return Repository.list(self.bb, workspace=self.slug)

    def repository(self, slug):
        return Repository(self.bb, workspace=self.slug, slug=slug)

