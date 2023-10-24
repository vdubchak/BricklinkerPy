import os
import logging

from rauth import OAuth1Service
import json

BL_CONSUMER_KEY = os.environ['BL_CONSUMER_KEY']
BL_CONSUMER_SECRET = os.environ['BL_CONSUMER_SECRET']
BL_ACCESS_TOKEN = os.environ['BL_ACCESS_TOKEN']
BL_TOKEN_SECRET = os.environ['BL_TOKEN_SECRET']


def processResponse(response, method, url, params):
    if 'meta' not in response:
        raise Exception('No meta and/or data key in response')
    meta = response['meta']
    if meta['code'] not in (200, 201, 204):
        if meta['message'] == 'INVALID_URI':
            raise Exception(meta['description'])

    data = response['data'] if 'data' in response else []

    return data


class ApiClient:
    def __init__(self):
        logging.debug('Initializing api client')

        self.service = OAuth1Service(name='bricklink',
                                     consumer_key=BL_CONSUMER_KEY,
                                     consumer_secret=BL_CONSUMER_SECRET,
                                     base_url='https://api.bricklink.com/api/store/v1/')
        logging.debug('Creating session')

        self.session = self.service.get_session((BL_ACCESS_TOKEN, BL_TOKEN_SECRET))

    def request(self, method, url, params):

        if method in ('POST', 'PUT', 'DELETE'):
            response = self.session.request(method, url, True, '', data=json.dumps(params),
                                            headers={'Content-Type': 'application/json'})
        else:
            response = self.session.request(method, url, True, '', params=params)
        responseJson = json.loads(response.content)
        return processResponse(responseJson, method, url, params)

    def get(self, url, params=None):
        if params is None:
            params = {}
        return self.request('GET', url, params)

    def post(self, url, params=None):
        if params is None:
            params = {}
        return self.request('POST', url, params)

    def put(self, url, params=None):
        if params is None:
            params = {}
        return self.request('PUT', url, params)

    def delete(self, url, params=None):
        if params is None:
            params = {}
        return self.request('DELETE', url, params)
