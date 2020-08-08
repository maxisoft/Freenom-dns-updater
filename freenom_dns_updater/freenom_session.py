import time
from typing import Optional
from urllib.parse import urlparse

import requests


class FreenomSession(requests.Session):
    last_request_time: float
    previous_url: Optional[str] = None
    request_cooldown = 1.5

    def __init__(self):
        super().__init__()
        self.last_request_time = time.monotonic()

    def request(self, method, url, *args, **kwargs):
        if abs(self.last_request_time - time.monotonic()) < self.request_cooldown:
            time.sleep(self.request_cooldown)
        res = super().request(method, url, *args, **kwargs)
        self.last_request_time = time.monotonic()
        self.previous_url = url
        return res

    def prepare_request(self, request: requests.Request):
        request = self._inject_headers(request)
        return super().prepare_request(request)

    def _inject_headers(self, request: requests.Request) -> requests.Request:
        if request.headers is None:
            request.headers = dict()

        if 'Host' not in request.headers:
            url = urlparse(request.url)
            request.headers['Host'] = url.hostname

        if 'Referer' not in request.headers:
            if self.previous_url is not None:
                request.headers['Referer'] = self.previous_url
            else:
                request.headers['Referer'] = request.url

        return request
