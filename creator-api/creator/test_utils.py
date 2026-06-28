import random
import httpx
from fastapi.testclient import TestClient
import factory
from .db import sm
from fastapi import FastAPI

app = FastAPI()

class APIClient:
    def __init__(self, app: FastAPI):
        self.client = TestClient(app)
        self.cookie = None
        self.csrf_cookie = None

    def open(self, method, url, *args, **kwargs):
        headers = kwargs.pop('headers', {})
        if 'json' in kwargs:  # API call
            assert 'data' not in kwargs, 'cannot set data and json at the same time'
            kwargs['data'] = kwargs.pop('json')
            headers['content-type'] = 'application/json'
        if self.cookie:
            if 'Cookie' not in headers:
                headers['Cookie'] = self.cookie
        if self.csrf_cookie:
            headers['X-CSRF-TOKEN'] = self.csrf_cookie

        response = self.client.request(method, url, headers=headers, *args, **kwargs)
        return response

    def logout(self):
        self.cookie = None
        self.csrf_cookie = None


class BoClient(APIClient):
    def login(self, username, password):
        resp = self.post('/v1/admin/login', json={
            'username': username,
            'password': password,
        })
        assert resp.status_code == 200, resp.json
        cookies = resp.headers.getlist('Set-Cookie')
        for cookie in cookies:
            if cookie.startswith('creator_auth_cookie='):
                self.cookie = cookie
            elif cookie.startswith('creator_auth_csrf_cookie='):
                self.csrf_cookie = cookie.replace(
                    'creator_auth_csrf_cookie=', '').split(';')[0]



class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = sm.get_db()


class Sequence(factory.Sequence):
    def __init__(self, namespace='', randomize=True):
        if randomize:
            prefix = '{}-{:05d}'.format(namespace, random.randint(0, 10000))
        else:
            prefix = namespace
        super().__init__(lambda n: f'{prefix}-{n}')