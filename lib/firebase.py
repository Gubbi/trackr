import urllib
import json
import httplib2

http = httplib2.Http()

class Firebase(object):

    def __init__(self, root_url, auth_token=None):
        self.root_url = root_url
        self.auth_token = auth_token

    # The methods set, push, update and remove are intended to mimic Firebase
    # API calls.

    def child(self, path):
        return Firebase(self.root_url + path, self.auth_token)

    def set(self, body):
        return self.put(body)

    def push(self, body):
        return self.post(body)

    def update(self, body):
        return self.patch(body)

    def remove(self):
        return self.delete()

    def get(self, params=None):
        return self._request('GET', params=params)

    def post(self, body):
        return self._request('POST', body=body)

    def put(self, body):
        return self._request('PUT', body=body)

    def patch(self, body):
        return self._request('PATCH', body=body)

    def delete(self):
        return self._request('DELETE')

    def _request(self, method, **kwargs):
        if 'body' in kwargs:
            kwargs['body'] = json.dumps(kwargs['body'])

        params = {}
        if 'params' in kwargs:
            if kwargs['params']:
                params.update(kwargs['params'])
            del kwargs['params']

        if self.auth_token:
            params.update({'auth': self.auth_token})

        # Do we need to chuck on some extra params?
        if params:
            url = '%s?%s' % (self.root_url, urllib.urlencode(params))
        else:
            url = self.root_url

        response, content = http.request(url, method, **kwargs)

        if response.status == 200:
            return json.loads(content)
        else:
            return None
